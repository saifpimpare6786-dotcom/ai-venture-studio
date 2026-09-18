import re
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings

try:
    import json_repair
except ImportError:
    json_repair = None

class LLMRouter:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.ollama_model = settings.OLLAMA_MODEL
        self.groq_keys = settings.groq_key_list
        self.nvidia_keys = settings.nvidia_key_list
        self.gemini_keys = settings.gemini_key_list
        
        self.groq_index = 0
        self.nvidia_index = 0
        self.gemini_index = 0
        
        # Sliding-window circuit breakers: False = Healthy, True = Tripped (Bypassed)
        self.circuit_breakers = {
            "gemini": False,
            "nvidia": False,
            "groq": False,
            "ollama": False
        }
        self.failure_counts = {
            "gemini": 0,
            "nvidia": 0,
            "groq": 0,
            "ollama": 0
        }

    def _rotate_key(self, provider: str) -> Optional[str]:
        if provider == "groq" and self.groq_keys:
            self.groq_index = (self.groq_index + 1) % len(self.groq_keys)
            return self.groq_keys[self.groq_index]
        elif provider == "nvidia" and self.nvidia_keys:
            self.nvidia_index = (self.nvidia_index + 1) % len(self.nvidia_keys)
            return self.nvidia_keys[self.nvidia_index]
        elif provider == "gemini" and self.gemini_keys:
            self.gemini_index = (self.gemini_index + 1) % len(self.gemini_keys)
            return self.gemini_keys[self.gemini_index]
        return None

    def _clean_json_output(self, text: str) -> str:
        """Strip <think> tags, markdown code fences, and extract valid JSON."""
        # 1. Strip Qwen <think>...</think> reasoning traces
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        # 2. Strip ```json ... ``` markdown code fences
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
        # 3. Direct JSON search
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    def _parse_json_robust(self, raw: str) -> Dict[str, Any]:
        """
        Parses JSON even if accompanied by markdown fences, <think> tags,
        preambles, or trailing extra data.
        """
        if not raw or not raw.strip():
            raise ValueError("Empty response received from LLM")

        cleaned = self._clean_json_output(raw)

        # 1. Try json_repair if available
        if json_repair:
            try:
                parsed = json_repair.loads(cleaned)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except Exception:
                pass

        # 2. Try standard json.loads
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # 3. Handle 'Extra data' using JSONDecoder raw_decode starting at first '{'
        start_idx = cleaned.find("{")
        if start_idx != -1:
            try:
                decoder = json.JSONDecoder()
                obj, _ = decoder.raw_decode(cleaned[start_idx:])
                if isinstance(obj, dict):
                    return obj
            except Exception:
                pass

        # 4. Extract between first '{' and last '}'
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx > start_idx:
            chunk = cleaned[start_idx:end_idx+1]
            try:
                parsed = json.loads(chunk)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                if json_repair:
                    try:
                        parsed = json_repair.loads(chunk)
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass

        raise ValueError(f"Failed to parse valid JSON object from model output: {raw[:200]}...")

    async def call_ollama(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4096) -> str:
        """Direct local inference with Ollama without grammar constraints."""
        async with httpx.AsyncClient(timeout=90.0) as client:
            payload = {
                "model": self.ollama_model,
                "messages": messages,
                "keep_alive": "24h",
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 16384
                },
                "stream": False
            }
            res = await client.post(f"{self.ollama_url}/api/chat", json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Ollama API returned status {res.status_code}: {res.text}")
            data = res.json()
            raw_content = data.get("message", {}).get("content", "")
            return self._clean_json_output(raw_content)

    async def call_gemini(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4096) -> str:
        if not self.gemini_keys or self.circuit_breakers["gemini"]:
            raise RuntimeError("Gemini unavailable or circuit breaker tripped")
        
        key = self.gemini_keys[self.gemini_index]
        contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
            
        model_candidates = [settings.GEMINI_MODEL, "gemini-2.5-flash"]
        model_candidates = list(dict.fromkeys(model_candidates))
        
        last_gemini_error = None
        async with httpx.AsyncClient(timeout=35.0) as client:
            for model_name in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
                res = await client.post(
                    url,
                    json={
                        "contents": contents,
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_tokens,
                            "responseMimeType": "application/json"
                        }
                    }
                )
                if res.status_code in (401, 403, 429):
                    self._rotate_key("gemini")
                    raise RuntimeError(f"Gemini rate limit/auth error: {res.status_code}")
                if res.status_code == 404:
                    last_gemini_error = f"Gemini model '{model_name}' not available (404)"
                    continue
                if res.status_code != 200:
                    raise RuntimeError(f"Gemini API error: {res.status_code} {res.text}")
                
                data = res.json()
                raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return self._clean_json_output(raw_text)
                
            raise RuntimeError(f"All Gemini models failed. Last error: {last_gemini_error}")

    async def call_nvidia(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4096) -> str:
        if not self.nvidia_keys or self.circuit_breakers["nvidia"]:
            raise RuntimeError("NVIDIA NIM unavailable or circuit breaker tripped")
        
        key = self.nvidia_keys[self.nvidia_index]
        async with httpx.AsyncClient(timeout=35.0) as client:
            res = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": settings.NVIDIA_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            if res.status_code in (401, 403, 429):
                self._rotate_key("nvidia")
                raise RuntimeError(f"NVIDIA NIM rate limit/auth error: {res.status_code}")
            if res.status_code != 200:
                raise RuntimeError(f"NVIDIA NIM error: {res.status_code} {res.text}")
            
            data = res.json()
            if not data.get("choices") or len(data["choices"]) == 0:
                raise RuntimeError(f"NVIDIA NIM returned empty response: {data}")
            return self._clean_json_output(data["choices"][0]["message"]["content"])

    async def call_groq(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 4096) -> str:
        if not self.groq_keys or self.circuit_breakers["groq"]:
            raise RuntimeError("Groq unavailable or circuit breaker tripped")
        
        key = self.groq_keys[self.groq_index]
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"}
                }
            )
            if res.status_code in (401, 403, 429):
                self._rotate_key("groq")
                raise RuntimeError(f"Groq rate limit/auth error: {res.status_code}")
            if res.status_code != 200:
                raise RuntimeError(f"Groq API error: {res.status_code} {res.text}")
            
            data = res.json()
            return self._clean_json_output(data["choices"][0]["message"]["content"])

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Tiered execution with automatic key rotation, circuit breakers, and local Ollama air-gap fallback.
        """
        messages = [
            {"role": "system", "content": system_prompt + "\n\nCRITICAL: You MUST respond ONLY with a valid JSON object adhering strictly to the schema requested. Do not include markdown preamble, commentary, or <think> tags outside the JSON."},
            {"role": "user", "content": user_prompt}
        ]

        providers = []
        if preferred_provider:
            providers.append(preferred_provider)
        
        if self.groq_keys:
            providers.append("groq")
        if self.gemini_keys:
            providers.append("gemini")
        if self.nvidia_keys:
            providers.append("nvidia")
        providers.append("ollama")

        providers = list(dict.fromkeys(providers))

        last_error = None
        for provider in providers:
            try:
                if provider == "gemini" and self.gemini_keys and not self.circuit_breakers["gemini"]:
                    raw = await self.call_gemini(messages, temperature, max_tokens)
                elif provider == "nvidia" and self.nvidia_keys and not self.circuit_breakers["nvidia"]:
                    raw = await self.call_nvidia(messages, temperature, max_tokens)
                elif provider == "groq" and self.groq_keys and not self.circuit_breakers["groq"]:
                    raw = await self.call_groq(messages, temperature, max_tokens)
                elif provider == "ollama":
                    raw = await self.call_ollama(messages, temperature, max_tokens)
                else:
                    continue

                parsed = self._parse_json_robust(raw)
                self.failure_counts[provider] = 0
                return parsed

            except Exception as e:
                last_error = e
                self.failure_counts[provider] = self.failure_counts.get(provider, 0) + 1
                if self.failure_counts[provider] >= 4:
                    self.circuit_breakers[provider] = True
                err_detail = str(e).strip() if str(e).strip() else f"{type(e).__name__} (check connectivity / API key / model availability)"
                print(f"[LLM Router] Provider '{provider}' error: {err_detail}. Trying next provider...")
                await asyncio.sleep(0.2)

        raise RuntimeError(f"All LLM providers exhausted. Last error: {last_error}")

llm_router = LLMRouter()
