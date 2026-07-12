import os
import sys
import httpx
from dotenv import load_dotenv

# Load env variables from root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def test_tavily_search(query: str):
    print("=== Tavily API Standalone Search Test ===")
    
    if not TAVILY_API_KEY:
        print("ERROR: TAVILY_API_KEY is not defined in the environment or .env file.")
        sys.exit(1)
        
    print(f"Loaded Tavily API Key: {TAVILY_API_KEY[:8]}...{TAVILY_API_KEY[-4:] if len(TAVILY_API_KEY) > 8 else ''}")
    print(f"Querying Tavily for: '{query}'\n")
    
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "include_answer": True
    }
    
    try:
        response = httpx.post("https://api.tavily.com/search", json=payload, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Received 200 OK from Tavily!")
            
            # Print Tavily AI Summary Answer if available
            answer = data.get("answer")
            if answer:
                print(f"\nTavily AI Answer Summary:\n{answer}\n")
                
            # Print individual search results
            results = data.get("results", [])
            print(f"Found {len(results)} search results:")
            for idx, result in enumerate(results):
                title = result.get("title", "No Title")
                url = result.get("url", "No URL")
                content = result.get("content", "")
                score = result.get("score", 0.0)
                
                print(f"\n[{idx + 1}] {title} (Score: {score})")
                print(f"    URL: {url}")
                print(f"    Snippet: {content[:150]}...")
                
        else:
            print(f"FAILURE: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error executing request: {str(e)}")

if __name__ == "__main__":
    search_query = "carbon accounting market size for SMEs in United States"
    test_tavily_search(search_query)
