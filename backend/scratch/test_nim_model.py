import sys, os
sys.path.append(os.path.abspath("."))
import httpx
from app.core.config import settings

def test_model(model_id):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Hello! Output 5 words."}],
        "temperature": 0.2,
        "max_tokens": 100
    }
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=20.0)
        res = resp.json()
        print("Message dict:", res["choices"][0]["message"])
        print("Extracted content:", res["choices"][0]["message"].get("content"))
    except Exception as e:
        print(f"Model: {model_id} -> Exception: {e}")

if __name__ == "__main__":
    test_model("deepseek-ai/deepseek-v4-flash")
    test_model("deepseek-ai/deepseek-r1")
    test_model("meta/llama-3.1-70b-instruct")
    test_model("meta/llama-3.3-70b-instruct")
