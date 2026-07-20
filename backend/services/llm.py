import time
import httpx
from typing import Dict, Any, Union
from app.core.config import settings

def call_gemini(prompt: str, system_prompt: str = None) -> str:
    """
    Calls the Gemini API (gemini-3.5-flash) with built-in 429 rate limit backoff.
    """
    # Pace requests to avoid API quota saturation (especially when called concurrently or sequentially)
    time.sleep(1.5)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    
    contents_part = []
    if system_prompt:
        contents_part.append({"text": f"System Instruction: {system_prompt}\n\nUser Input: {prompt}"})
    else:
        contents_part.append({"text": prompt})
        
    payload = {
        "contents": [{"parts": contents_part}]
    }
    
    max_retries = 3
    backoff = 1.0
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

def call_nvidia_nim(prompt: str, system_prompt: str = None) -> str:
    """
    Calls the NVIDIA NIM API (meta/llama-3.1-70b-instruct) with built-in 429 rate limit backoff.
    """
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": "meta/llama-3.1-70b-instruct",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1024
    }
    
    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            # Increased timeout from 60.0 to 90.0 to reduce timeouts under heavy concurrent load
            response = httpx.post(url, json=payload, headers=headers, timeout=90.0)
            if response.status_code == 200:
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                print(f"NVIDIA NIM 429 rate limit hit. Attempt {attempt + 1}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
            else:
                raise ValueError(f"NVIDIA NIM error (Status {response.status_code}): {response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(backoff)
            backoff *= 2.0
            
    raise RuntimeError("NVIDIA NIM call failed after maximum retries.")

def call_llm(
    prompt: str,
    system_prompt: str = None,
    preferred_provider: str = "nvidia",
    project_id: str = None,
    agent_name: str = None
) -> Union[str, Dict[str, Any]]:
    """
    Wrapper offering failover. If preferred model provider fails,
    it automatically falls back to the other model provider.
    If BOTH providers fail, it does not raise an exception — instead:
      1. Logs the failure transaction to Supabase agent_logs (if project_id & agent_name are passed).
      2. Returns a structured error dictionary: {"status": "failed", "error": "Error details..."}
    """
    primary_err = None
    fallback_err = None

    if preferred_provider == "nvidia":
        # 1. Execute NIM primary
        try:
            return call_nvidia_nim(prompt, system_prompt)
        except Exception as e:
            primary_err = str(e)
            print(f"WARNING: NVIDIA NIM failed. Falling back to Gemini API. Error: {primary_err}")
        
        # 2. Execute Gemini fallback
        try:
            return call_gemini(prompt, system_prompt)
        except Exception as e:
            fallback_err = str(e)
            print(f"ERROR: Gemini fallback also failed. Error: {fallback_err}")
    else:
        # 1. Execute Gemini primary
        try:
            return call_gemini(prompt, system_prompt)
        except Exception as e:
            primary_err = str(e)
            print(f"WARNING: Gemini API failed. Falling back to NVIDIA NIM. Error: {primary_err}")
        
        # 2. Execute NIM fallback
        try:
            return call_nvidia_nim(prompt, system_prompt)
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
