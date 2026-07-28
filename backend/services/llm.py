import time
import httpx
from typing import Dict, Any, Union
from app.core.config import settings

def call_gemini(
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = 2048,
    response_schema: dict = None,
    json_mode: bool = False,
) -> str:
    """
    Calls the Gemini API (gemini-3.5-flash) with built-in 429 rate limit backoff.

    Args:
        max_tokens: Maximum output tokens for the completion. Passed as
                    generationConfig.maxOutputTokens in the Gemini REST payload.
                    Default 2048. Long-form reports (Business Plan) should pass 8192.
        response_schema: Optional JSON schema dict to enforce output shape at API level.
        json_mode: If True, sets responseMimeType to application/json.
    """
    # Pace requests to avoid API quota saturation (especially when called concurrently or sequentially)
    time.sleep(1.5)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    
    contents_part = []
    if system_prompt:
        contents_part.append({"text": f"System Instruction: {system_prompt}\n\nUser Input: {prompt}"})
    else:
        contents_part.append({"text": prompt})
        
    gen_config: Dict[str, Any] = {
        "maxOutputTokens": max_tokens,
    }
    if response_schema or json_mode:
        gen_config["responseMimeType"] = "application/json"
    if response_schema:
        gen_config["responseSchema"] = response_schema

    payload = {
        "contents": [{"parts": contents_part}],
        "generationConfig": gen_config,
    }
    
    max_retries = 5
    backoff = 2.0
    for attempt in range(max_retries):
        try:
            response = httpx.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60.0)
            if response.status_code == 200:
                res_data = response.json()
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
            elif response.status_code == 404:
                print(f"Gemini API 404 (Model Not Found) error. Bypassing retries to failover immediately.")
                raise ValueError(f"Gemini API returned 404: {response.text}")
            elif response.status_code == 429:
                print(f"Gemini API 429 rate limit hit. Attempt {attempt + 1}. Retrying in {backoff + 2.0}s...")
                time.sleep(backoff + 2.0) # Add delay to avoid back-to-back hits
                backoff *= 2.0
            else:
                raise ValueError(f"Gemini API error (Status {response.status_code}): {response.text}")
        except Exception as e:
            if "404" in str(e):
                raise e
            if attempt == max_retries - 1:
                raise e
            print(f"Gemini call exception encountered. Retrying in {backoff + 2.0}s... Error: {str(e)}")
            time.sleep(backoff + 2.0) # Add delay to avoid back-to-back hits
            backoff *= 2.0
            
    raise RuntimeError("Gemini API call failed after maximum retries.")

# Dynamic NIM model routing dictionary mapping agent types to optimized NVIDIA NIM models
NIM_MODEL_ROUTING: Dict[str, str] = {
    "Strategy Agent": "moonshotai/kimi-k2.6",
    "Orchestrator Agent": "moonshotai/kimi-k2.6",
    "Marketing Agent": "deepseek-ai/deepseek-v4-flash",
    "default": "meta/llama-3.1-70b-instruct",
}

def call_nvidia_nim(
    prompt: str,
    system_prompt: str = None,
    agent_name: str = None,
    max_tokens: int = 2048,
    json_mode: bool = False,
    response_format: dict = None,
) -> str:
    """
    Calls the NVIDIA NIM API with built-in 429 rate limit backoff and dynamic model routing.
    
    Args:
        agent_name: Agent name or type used to dispatch to specific NIM models.
        max_tokens: Token budget for completion. Default 2048. Auto-bumped to 8192 if agent_name
                    contains "report" or "council".
        json_mode: If True, sets response_format to {"type": "json_object"}.
        response_format: Custom response format payload for structured output.
    """
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Resolve model via dynamic routing dictionary
    model_id = NIM_MODEL_ROUTING.get(agent_name, NIM_MODEL_ROUTING["default"]) if agent_name else NIM_MODEL_ROUTING["default"]
    print(f"[NVIDIA NIM] Dispatching call for '{agent_name or 'Unspecified'}' -> Model: '{model_id}'")
    
    # Adjust max_tokens: default 2048, bump to 8192 if agent_name contains "report" or "council"
    if agent_name and any(k in agent_name.lower() for k in ("report", "council")):
        if max_tokens < 8192:
            max_tokens = 8192
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload: Dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    if response_format:
        payload["response_format"] = response_format
    elif json_mode:
        payload["response_format"] = {"type": "json_object"}
    
    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            # Increased timeout from 90.0 to 120.0 to reduce timeouts under heavy concurrent load
            response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
            if response.status_code == 200:
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                print(f"NVIDIA NIM 429 rate limit hit ({model_id}). Attempt {attempt + 1}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
            else:
                raise ValueError(f"NVIDIA NIM error (Status {response.status_code}): {response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(backoff)
            backoff *= 2.0
            
    raise RuntimeError(f"NVIDIA NIM call failed after maximum retries for model {model_id}.")

# Per-run Gemini Circuit Breaker state
_gemini_consecutive_failures: int = 0
_gemini_marked_down: bool = False

def reset_gemini_circuit_breaker() -> None:
    """Resets the per-run Gemini circuit breaker state for a new pipeline run."""
    global _gemini_consecutive_failures, _gemini_marked_down
    _gemini_consecutive_failures = 0
    _gemini_marked_down = False
    print("[Circuit Breaker] Reset Gemini circuit breaker for new pipeline run.")

def is_gemini_marked_down() -> bool:
    """Returns True if Gemini is currently marked DOWN for this pipeline run."""
    return _gemini_marked_down

def _record_gemini_success() -> None:
    """Resets consecutive failures when a Gemini call succeeds."""
    global _gemini_consecutive_failures
    _gemini_consecutive_failures = 0

def _record_gemini_failure() -> None:
    """Increments failure count and trips circuit breaker if threshold reached (>= 2)."""
    global _gemini_consecutive_failures, _gemini_marked_down
    _gemini_consecutive_failures += 1
    if _gemini_consecutive_failures >= 2 and not _gemini_marked_down:
        _gemini_marked_down = True
        print("[Circuit Breaker] Gemini marked DOWN for this run — routing NVIDIA-primary.")

def call_llm(
    prompt: str,
    system_prompt: str = None,
    preferred_provider: str = "nvidia",
    project_id: str = None,
    agent_name: str = None,
    max_tokens: int = 2048,
    response_schema: dict = None,
    json_mode: bool = False,
) -> Union[str, Dict[str, Any]]:
    """
    Wrapper offering failover. If preferred model provider fails,
    it automatically falls back to the other model provider.
    If BOTH providers fail, it does not raise an exception — instead:
      1. Logs the failure transaction to Supabase agent_logs (if project_id & agent_name are passed).
      2. Returns a structured error dictionary: {"status": "failed", "error": "Error details..."}
    
    Args:
        max_tokens: Completion token budget passed to NVIDIA NIM. Default 2048 is fine for
                    agent reasoning nodes. Long-form reports (Business Plan etc.) pass 8192.
        response_schema: Optional JSON schema dict passed to Gemini.
        json_mode: If True, enforces JSON mode / MIME type on model APIs.
    """
    primary_err = None
    fallback_err = None

    effective_provider = preferred_provider
    if preferred_provider == "gemini" and _gemini_marked_down:
        print("[Circuit Breaker] Gemini marked DOWN for this run — routing NVIDIA-primary.")
        effective_provider = "nvidia"

    if effective_provider == "nvidia":
        # 1. Execute NIM primary
        try:
            return call_nvidia_nim(
                prompt, system_prompt, agent_name=agent_name, max_tokens=max_tokens, json_mode=json_mode
            )
        except Exception as e:
            primary_err = str(e)
            print(f"WARNING: NVIDIA NIM failed. Falling back to Gemini API. Error: {primary_err}")
        
        # 2. Execute Gemini fallback (only if Gemini is not marked DOWN)
        if not _gemini_marked_down:
            try:
                res = call_gemini(
                    prompt, system_prompt, max_tokens=max_tokens,
                    response_schema=response_schema, json_mode=json_mode
                )
                _record_gemini_success()
                return res
            except Exception as e:
                fallback_err = str(e)
                print(f"ERROR: Gemini fallback also failed. Error: {fallback_err}")
                _record_gemini_failure()
        else:
            fallback_err = "Gemini marked DOWN (bypassed fallback)."
    else:
        # 1. Execute Gemini primary
        try:
            res = call_gemini(
                prompt, system_prompt, max_tokens=max_tokens,
                response_schema=response_schema, json_mode=json_mode
            )
            _record_gemini_success()
            return res
        except Exception as e:
            primary_err = str(e)
            print(f"WARNING: Gemini API failed. Falling back to NVIDIA NIM. Error: {primary_err}")
            _record_gemini_failure()
        
        # 2. Execute NIM fallback
        try:
            return call_nvidia_nim(
                prompt, system_prompt, agent_name=agent_name, max_tokens=max_tokens, json_mode=json_mode
            )
        except Exception as e:
            fallback_err = str(e)
            print(f"ERROR: NVIDIA NIM fallback also failed. Error: {fallback_err}")

    # 3. Dual provider failure cleanup & DB logging
    combined_error = f"LLM Call Failed. Primary ({preferred_provider}): {primary_err}. Fallback: {fallback_err}."
    
    if project_id and agent_name:
        try:
            from app.database.supabase import get_supabase_client
            supabase = get_supabase_client()
            supabase.table("agent_logs").insert({
                "project_id": project_id,
                "agent_name": agent_name,
                "status": "failed",
                "input_data": {
                    "prompt_preview": prompt[:300],
                    "preferred_provider": preferred_provider
                },
                "output_data": {
                    "error": combined_error
                }
            }).execute()
            print(f"Logged LLM failure for '{agent_name}' to Supabase agent_logs.")
        except Exception as db_err:
            print(f"Failed to log LLM failure to Supabase: {str(db_err)}")

    return {
        "status": "failed",
        "error": combined_error
    }

