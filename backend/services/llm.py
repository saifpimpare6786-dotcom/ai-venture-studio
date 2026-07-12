import time
import httpx
from app.core.config import settings

def call_gemini(prompt: str, system_prompt: str = None) -> str:
    """
    Calls the Gemini API (gemini-1.5-flash) with built-in 429 rate limit backoff.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    
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
            response = httpx.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30.0)
            if response.status_code == 200:
                res_data = response.json()
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
            elif response.status_code == 429:
                print(f"Gemini API 429 rate limit hit. Attempt {attempt + 1}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
            else:
                raise ValueError(f"Gemini API error (Status {response.status_code}): {response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(backoff)
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
            response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
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

def call_llm(prompt: str, system_prompt: str = None, preferred_provider: str = "nvidia") -> str:
    """
    Wrapper offering failover. If preferred model provider fails (e.g. 429 rate-limited),
    it automatically falls back to the other model provider.
    """
    if preferred_provider == "nvidia":
        try:
            return call_nvidia_nim(prompt, system_prompt)
        except Exception as e:
            print(f"WARNING: NVIDIA NIM failed. Falling back to Gemini API. Error: {str(e)}")
            return call_gemini(prompt, system_prompt)
    else:
        try:
            return call_gemini(prompt, system_prompt)
        except Exception as e:
            print(f"WARNING: Gemini API failed. Falling back to NVIDIA NIM. Error: {str(e)}")
            return call_nvidia_nim(prompt, system_prompt)
