import time
import httpx
import re
from typing import Dict, Any, Union, List, Tuple
from app.core.config import settings

# Per-run Provider Key Rotation State
_groq_key_index: int = 0
_nvidia_key_index: int = 0
_gemini_key_index: int = 0
_groq_exhausted_indices: set = set()
_nvidia_exhausted_indices: set = set()
_gemini_exhausted_indices: set = set()

def reset_llm_key_rotation() -> None:
    """Resets key indices and exhausted key sets for Groq, NVIDIA NIM, and Gemini."""
    global _groq_key_index, _nvidia_key_index, _gemini_key_index
    global _groq_exhausted_indices, _nvidia_exhausted_indices, _gemini_exhausted_indices
    _groq_key_index = 0
    _nvidia_key_index = 0
    _gemini_key_index = 0
    _groq_exhausted_indices = set()
    _nvidia_exhausted_indices = set()
    _gemini_exhausted_indices = set()

def _get_active_groq_key() -> Tuple[int, str]:
    """Returns (key_index, api_key) for the current active Groq key, or raises RuntimeError if all exhausted."""
    keys = settings.get_groq_keys()
    if not keys:
        raise RuntimeError("No Groq API keys configured.")
    global _groq_key_index, _groq_exhausted_indices
    num_keys = len(keys)
    for i in range(num_keys):
        idx = (_groq_key_index + i) % num_keys
        if idx not in _groq_exhausted_indices:
            _groq_key_index = idx
            return (idx, keys[idx])
    raise RuntimeError(f"All {num_keys} Groq API key(s) exhausted for this run.")

def _mark_groq_key_exhausted(idx: int, reason: str) -> None:
    """Marks Groq key as exhausted and advances key index."""
    global _groq_key_index, _groq_exhausted_indices
    _groq_exhausted_indices.add(idx)
    keys = settings.get_groq_keys()
    num_keys = len(keys)
    
    next_idx = None
    for i in range(num_keys):
        cand = (idx + 1 + i) % num_keys
        if cand not in _groq_exhausted_indices:
            next_idx = cand
            break
            
    if next_idx is not None:
        _groq_key_index = next_idx
        print(f"[Key Rotation] Groq key {idx + 1} {reason} — rotating to key {next_idx + 1}")
    else:
        print(f"[Key Rotation] Groq key {idx + 1} {reason} — ALL {num_keys} Groq key(s) exhausted for this run.")

def _get_active_nvidia_key() -> Tuple[int, str]:
    """Returns (key_index, api_key) for the current active NVIDIA key, or raises RuntimeError if all exhausted."""
    keys = settings.get_nvidia_keys()
    if not keys:
        raise RuntimeError("No NVIDIA NIM API keys configured.")
    global _nvidia_key_index, _nvidia_exhausted_indices
    num_keys = len(keys)
    for i in range(num_keys):
        idx = (_nvidia_key_index + i) % num_keys
        if idx not in _nvidia_exhausted_indices:
            _nvidia_key_index = idx
            return (idx, keys[idx])
    raise RuntimeError(f"All {num_keys} NVIDIA API key(s) exhausted for this run.")

def _mark_nvidia_key_exhausted(idx: int, reason: str) -> None:
    """Marks NVIDIA key as exhausted and advances key index."""
    global _nvidia_key_index, _nvidia_exhausted_indices
    _nvidia_exhausted_indices.add(idx)
    keys = settings.get_nvidia_keys()
    num_keys = len(keys)
    
    next_idx = None
    for i in range(num_keys):
        cand = (idx + 1 + i) % num_keys
        if cand not in _nvidia_exhausted_indices:
            next_idx = cand
            break
            
    if next_idx is not None:
        _nvidia_key_index = next_idx
        print(f"[Key Rotation] NVIDIA key {idx + 1} {reason} — rotating to key {next_idx + 1}")
    else:
        print(f"[Key Rotation] NVIDIA key {idx + 1} {reason} — ALL {num_keys} NVIDIA key(s) exhausted for this run.")

def _get_active_gemini_key() -> Tuple[int, str]:
    """Returns (key_index, api_key) for the current active Gemini key, or raises RuntimeError if all exhausted."""
    keys = settings.get_gemini_keys()
    if not keys:
        raise RuntimeError("No Gemini API keys configured.")
    global _gemini_key_index, _gemini_exhausted_indices
    num_keys = len(keys)
    for i in range(num_keys):
        idx = (_gemini_key_index + i) % num_keys
        if idx not in _gemini_exhausted_indices:
            _gemini_key_index = idx
            return (idx, keys[idx])
    raise RuntimeError(f"All {num_keys} Gemini API key(s) exhausted for this run.")

def _mark_gemini_key_exhausted(idx: int, reason: str) -> None:
    """Marks Gemini key as exhausted and advances key index."""
    global _gemini_key_index, _gemini_exhausted_indices
    _gemini_exhausted_indices.add(idx)
    keys = settings.get_gemini_keys()
    num_keys = len(keys)
    
    next_idx = None
    for i in range(num_keys):
        cand = (idx + 1 + i) % num_keys
        if cand not in _gemini_exhausted_indices:
            next_idx = cand
            break
            
    if next_idx is not None:
        _gemini_key_index = next_idx
        print(f"[Key Rotation] Gemini key {idx + 1} {reason} — rotating to key {next_idx + 1}")
    else:
        print(f"[Key Rotation] Gemini key {idx + 1} {reason} — ALL {num_keys} Gemini key(s) exhausted for this run.")

def call_gemini(
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = 2048,
    response_schema: dict = None,
    json_mode: bool = False,
) -> str:
    """
    Calls the Gemini API (gemini-3.5-flash) with built-in key rotation and 429 rate limit backoff.

    Args:
        max_tokens: Maximum output tokens for the completion. Passed as
                    generationConfig.maxOutputTokens in the Gemini REST payload.
                    Default 2048. Long-form reports (Business Plan) should pass 8192.
        response_schema: Optional JSON schema dict to enforce output shape at API level.
        json_mode: If True, sets responseMimeType to application/json.
    """
    time.sleep(1.5)
    
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

    while True:
        key_idx, api_key = _get_active_gemini_key()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
        
        max_retries = 5
        backoff = 2.0
        key_rotated = False

        for attempt in range(max_retries):
            try:
                response = httpx.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60.0)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["candidates"][0]["content"]["parts"][0]["text"]
                elif response.status_code in (400, 401, 403, 429):
                    reason = f"quota-exhausted ({response.status_code})" if response.status_code == 429 else f"auth/key error ({response.status_code})"
                    _mark_gemini_key_exhausted(key_idx, reason)
                    key_rotated = True
                    break  # Break retry loop to try call with NEXT rotated key
                elif response.status_code == 404:
                    print(f"Gemini API 404 (Model Not Found) error. Bypassing retries to failover immediately.")
                    raise ValueError(f"Gemini API returned 404: {response.text}")
                else:
                    raise ValueError(f"Gemini API error (Status {response.status_code}): {response.text}")
            except Exception as e:
                if key_rotated:
                    break
                if "404" in str(e):
                    raise e
                if attempt == max_retries - 1:
                    raise e
                print(f"Gemini call exception encountered. Retrying in {backoff + 2.0}s... Error: {str(e)}")
                time.sleep(backoff + 2.0)
                backoff *= 2.0

        if not key_rotated:
            raise RuntimeError("Gemini API call failed after maximum retries.")

# Toggleable flag for DeepSeek-v4-pro thinking mode (disabled by default; retained as optional enhancement)
ENABLE_DEEPSEEK_THINKING_MODE: bool = False

# Dynamic NIM model routing dictionary mapping agent types to optimized NVIDIA NIM models
NIM_MODEL_ROUTING: Dict[str, str] = {
    "default": "meta/llama-3.1-70b-instruct",
}

def print_nim_model_dispatch_table() -> None:
    """Prints the exhaustive 13-agent -> model dispatch table at startup."""
    pipeline_nodes = [
        ("Planning Agent", "LLM"),
        ("Orchestrator Agent", "LLM"),
        ("Research Agent", "LLM"),
        ("Finance Agent", "LLM"),
        ("Strategy Agent", "LLM"),
        ("Marketing Agent", "LLM"),
        ("Risk Agent", "LLM"),
        ("Council Agent", "LLM"),
        ("Reviewer Agent", "LLM"),
        ("Critic Agent", "LLM"),
        ("Business Rules Engine", "LLM"),
        ("Analytics & Scoring", "LLM"),
        ("Report Generator", "LLM"),
    ]
    print("\n==========================================================================")
    print("=== AI VENTURE STUDIO — NVIDIA NIM MODEL DISPATCH ROUTING TABLE ===")
    print("==========================================================================")
    print(f"{'Agent / Node':<30} | {'Assigned Model / Engine':<42}")
    print("-" * 75)
    for node_name, node_type in pipeline_nodes:
        model = NIM_MODEL_ROUTING.get(node_name, NIM_MODEL_ROUTING["default"])
        thinking_suffix = ""
        if model == "deepseek-ai/deepseek-v4-pro":
            thinking_suffix = " [thinking-mode ON]" if ENABLE_DEEPSEEK_THINKING_MODE else " [thinking-mode OFF]"
        model_display = f"{model}{thinking_suffix}"
        print(f"{node_name:<30} | {model_display:<42}")
    print("==========================================================================\n")

def call_nvidia_nim(
    prompt: str,
    system_prompt: str = None,
    agent_name: str = None,
    max_tokens: int = 2048,
    json_mode: bool = False,
    response_format: dict = None,
) -> str:
    """
    Calls the NVIDIA NIM API with built-in key rotation, 429 rate limit backoff, and dynamic model routing.
    
    Args:
        agent_name: Agent name or type used to dispatch to specific NIM models.
        max_tokens: Token budget for completion. Default 2048. Auto-bumped to 8192 if agent_name
                    contains "report" or "council".
        json_mode: If True, sets response_format to {"type": "json_object"}.
        response_format: Custom response format payload for structured output.
    """
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    model_id = NIM_MODEL_ROUTING.get(agent_name, NIM_MODEL_ROUTING["default"]) if agent_name else NIM_MODEL_ROUTING["default"]
    print(f"[NVIDIA NIM] Dispatching call for '{agent_name or 'Unspecified'}' -> Model: '{model_id}'")
    
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
    if model_id == "deepseek-ai/deepseek-v4-pro" and ENABLE_DEEPSEEK_THINKING_MODE:
        payload["chat_template_kwargs"] = {"enable_thinking": True}
        print(f"[NVIDIA NIM] Enabled DeepSeek thinking-mode for '{agent_name}'")

    if response_format:
        payload["response_format"] = response_format
    elif json_mode:
        payload["response_format"] = {"type": "json_object"}

    while True:
        key_idx, api_key = _get_active_nvidia_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        backoff = 1.0
        key_rotated = False
        
        for attempt in range(max_retries):
            try:
                response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["choices"][0]["message"]["content"]
                elif response.status_code in (400, 401, 403, 429):
                    reason = f"quota-exhausted ({response.status_code})" if response.status_code == 429 else f"auth/key error ({response.status_code})"
                    _mark_nvidia_key_exhausted(key_idx, reason)
                    key_rotated = True
                    break  # Break retry loop to try call with NEXT rotated key
                else:
                    raise ValueError(f"NVIDIA NIM error (Status {response.status_code}): {response.text}")
            except Exception as e:
                if key_rotated:
                    break
                if attempt == max_retries - 1:
                    raise e
                time.sleep(backoff)
                backoff *= 2.0

        if not key_rotated:
            raise RuntimeError(f"NVIDIA NIM call failed after maximum retries for model {model_id}.")

def call_groq(
    prompt: str,
    system_prompt: str = None,
    agent_name: str = None,
    max_tokens: int = 2048,
    json_mode: bool = False,
    response_format: dict = None,
) -> str:
    """
    Calls the Groq API (llama-3.3-70b-versatile) with built-in key rotation and rate limit handling.
    
    Args:
        agent_name: Agent name or type (for logging/context).
        max_tokens: Token budget for completion. Default 2048. Auto-bumped to 8192 if agent_name
                    contains "report" or "council".
        json_mode: If True, sets response_format to {"type": "json_object"}.
        response_format: Custom response format payload for structured output.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    model_id = "llama-3.3-70b-versatile"
    print(f"[Groq] Dispatching call -> llama-3.3-70b-versatile")
    
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

    while True:
        key_idx, api_key = _get_active_groq_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        backoff = 1.0
        key_rotated = False
        
        for attempt in range(max_retries):
            try:
                response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["choices"][0]["message"]["content"]
                elif response.status_code in (400, 401, 403, 429):
                    reason = f"quota-exhausted ({response.status_code})" if response.status_code == 429 else f"auth/key error ({response.status_code})"
                    _mark_groq_key_exhausted(key_idx, reason)
                    key_rotated = True
                    break  # Break retry loop to try call with NEXT rotated key
                else:
                    raise ValueError(f"Groq API error (Status {response.status_code}): {response.text}")
            except Exception as e:
                if key_rotated:
                    break
                if attempt == max_retries - 1:
                    raise e
                time.sleep(backoff)
                backoff *= 2.0

        if not key_rotated:
            raise RuntimeError(f"Groq API call failed after maximum retries for model {model_id}.")

def _clean_ollama_qwen_response(raw_text: str, json_mode: bool = False) -> str:
    """
    Cleans raw response from local Qwen3 model:
    - Strips anything inside <think>...</think> tags.
    - Strips anything before the first '{' or '[' and after the last '}' or ']' if json_mode is True or braces exist.
    """
    text = re.sub(r'<think>.*?</think>', '', str(raw_text or ''), flags=re.DOTALL).strip()
    
    if json_mode or ('{' in text and '}' in text) or ('[' in text and ']' in text):
        first_brace = -1
        for i, char in enumerate(text):
            if char in ('{', '['):
                first_brace = i
                break
        last_brace = -1
        for i in range(len(text) - 1, -1, -1):
            if text[i] in ('}', ']'):
                last_brace = i
                break
        if first_brace != -1 and last_brace != -1 and last_brace >= first_brace:
            text = text[first_brace:last_brace + 1]
            
    return text

def call_ollama(
    prompt: str,
    system_prompt: str = None,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Calls the local Ollama API (qwen3:8b) via /api/generate as a 3rd last-resort fallback.
    Passes "think": false to disable reasoning monologue, and cleans <think> tags & non-JSON boundaries.
    """
    base_url = settings.OLLAMA_BASE_URL.rstrip('/')
    url = f"{base_url}/api/generate"
    
    payload: Dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
    }
    if system_prompt:
        payload["system"] = system_prompt
    if json_mode:
        payload["format"] = "json"

    max_retries = 2
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = httpx.post(url, json=payload, timeout=120.0)
            if response.status_code == 200:
                res_data = response.json()
                raw_text = res_data.get("response", "")
                return _clean_ollama_qwen_response(raw_text, json_mode=json_mode)
            else:
                raise ValueError(f"Ollama API error (Status {response.status_code}): {response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(backoff)
            backoff *= 2.0

    raise RuntimeError(f"Ollama API call failed for model {settings.OLLAMA_MODEL}.")

# Per-run Gemini Circuit Breaker state
_gemini_consecutive_failures: int = 0
_gemini_marked_down: bool = False

def reset_gemini_circuit_breaker() -> None:
    """Resets the per-run Gemini circuit breaker state and key rotation pools for a new pipeline run."""
    global _gemini_consecutive_failures, _gemini_marked_down
    _gemini_consecutive_failures = 0
    _gemini_marked_down = False
    reset_llm_key_rotation()
    print("[Circuit Breaker] Reset Gemini circuit breaker and key rotation pools for new pipeline run.")

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
    Wrapper offering multi-provider failover: Groq (PRIMARY) -> NVIDIA NIM / Gemini -> Ollama (Local).
    If preferred model provider fails, it automatically falls back through the provider chain.
    If ALL providers fail, it does not raise an exception — instead:
      1. Logs the failure transaction to Supabase agent_logs (if project_id & agent_name are passed).
      2. Returns a structured error dictionary: {"status": "failed", "error": "Error details..."}
    """
    groq_err = None
    primary_err = None
    fallback_err = None
    ollama_err = None

    # 1. Execute Groq primary cloud call (First in chain)
    try:
        resp_fmt = response_schema if (isinstance(response_schema, dict) and "type" in response_schema) else None
        return call_groq(
            prompt,
            system_prompt=system_prompt,
            agent_name=agent_name,
            max_tokens=max_tokens,
            json_mode=json_mode,
            response_format=resp_fmt
        )
    except Exception as e:
        groq_err = str(e)
        print(f"WARNING: Groq API failed. Falling back to secondary cloud provider. Error: {groq_err}")

    # 2. Existing cloud provider failover chain (NVIDIA NIM / Gemini)
    effective_provider = preferred_provider
    if preferred_provider == "gemini" and _gemini_marked_down:
        print("[Circuit Breaker] Gemini marked DOWN for this run — routing NVIDIA-primary.")
        effective_provider = "nvidia"

    if effective_provider == "nvidia":
        # Execute NIM primary
        try:
            return call_nvidia_nim(
                prompt, system_prompt, agent_name=agent_name, max_tokens=max_tokens, json_mode=json_mode
            )
        except Exception as e:
            primary_err = str(e)
            print(f"WARNING: NVIDIA NIM failed. Falling back to Gemini API. Error: {primary_err}")
        
        # Execute Gemini fallback (only if Gemini is not marked DOWN)
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
        # Execute Gemini primary
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
        
        # Execute NIM fallback
        try:
            return call_nvidia_nim(
                prompt, system_prompt, agent_name=agent_name, max_tokens=max_tokens, json_mode=json_mode
            )
        except Exception as e:
            fallback_err = str(e)
            print(f"ERROR: NVIDIA NIM fallback also failed. Error: {fallback_err}")

    # 3. Last-resort tertiary fallback to local Ollama (qwen3:8b) when ALL cloud providers fail
    print(f"[Local Fallback] Cloud exhausted — using local Ollama {settings.OLLAMA_MODEL}")
    try:
        return call_ollama(
            prompt, system_prompt=system_prompt, max_tokens=max_tokens, json_mode=json_mode
        )
    except Exception as e:
        ollama_err = str(e)
        print(f"ERROR: Local Ollama fallback also failed. Error: {ollama_err}")

    # 4. Multi-provider failure cleanup & DB logging
    combined_error = f"LLM Call Failed. Groq: {groq_err}. Primary ({effective_provider}): {primary_err}. Secondary: {fallback_err}. Tertiary (Ollama): {ollama_err}."
    
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
