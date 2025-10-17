import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from urllib.parse import urlparse 
import os, sys
import httpx 
from decouple import config 
from pydantic import BaseModel # For structured data input

# Ensure local modules are findable
if __name__ != "__main__":
    # Standard import for production/uvicorn runner
    from reputation_data import LOW_REPUTATION_DOMAINS 
else:
    # Custom import hack for running via `python main.py` for development
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from reputation_data import LOW_REPUTATION_DOMAINS 

# --- New Model Definition to receive data from the extension (MUST MATCH FRONTEND) ---
class LinkData(BaseModel):
    url: str
    domain: str

class CredibilityPayload(BaseModel):
    links: List[LinkData]
    query: Optional[str] = None # The user's original search term

# --- 1. FastAPI App Initialization & Config ---
app = FastAPI()

# Get API Key securely from the .env file
API_KEY = config('GOOGLE_FACT_CHECK_API_KEY', default='YOUR_FALLBACK_KEY')
FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


# --- 2. CORS Configuration (CRITICAL) ---
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://www.google.com",
    "https://*.google.com",    
    "chrome-extension://*",    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- 3. The Core MVP Logic (Combined Domain + API Check) ---
# NOTE: The input type now uses the Pydantic model CredibilityPayload
@app.post("/api/check-credibility")
async def check_credibility(payload: CredibilityPayload): 
    
    response_data = []
    
    # Check 1: Fact Check API (Only run once using the user's search query)
    fact_check_verdict = None
    
    print(f"\n[BACKEND] User Search Query: {payload.query}")
    
    if payload.query and API_KEY != 'YOUR_FALLBACK_KEY':
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "query": payload.query, # 💥 FIX: Use the user's query here 💥
                    "key": API_KEY,
                    "pageSize": 1 
                }
                response = await client.get(FACT_CHECK_URL, params=params)
                response.raise_for_status() 
                
                data = response.json()
                
                if data.get('claims'):
                    claim_review = data['claims'][0]['claimReview'][0]
                    rating_text = claim_review.get('textualRating', 'RATED')
                    publisher = claim_review['publisher']['name']
                    
                    # 💥 FIX: Implement the Ambiguity Solution (Topic Warning) 💥
                    verdict = f"Fact Checked CLAIM: {rating_text}"
                    label = f"CLAIM RATED {rating_text.upper()} by {publisher}"
                    
                    # Store the result to be applied to all links
                    fact_check_verdict = {
                        "verdict": verdict,
                        "label": label,
                        # No need to send the review_url yet, keeping it simple
                    }
                    print(f"[API CHECK] Match Found: {rating_text} by {publisher}")
                else:
                    print("[API CHECK] No direct fact-check found for this exact query.")

        except httpx.HTTPStatusError as e:
            print(f"[API Error] Status {e.response.status_code} - Check API access/billing.")
        except Exception:
            print("[API Error] Could not process API response.")


    # Apply verdicts to ALL links
    print(f"[BACKEND] Applying checks to {len(payload.links)} links.")
    for item in payload.links:
        url = item.url
        domain_root = None
        verdict = "Unassessed"
        label = "No Fact Check Found"
        
        try:
            domain = urlparse(url).netloc.replace('www.', '')
            domain_root = domain
        except Exception:
            pass 

        # --- Priority 1: Fact Check API Verdict (Apply to all links if found) ---
        if fact_check_verdict:
            verdict = fact_check_verdict['verdict']
            label = fact_check_verdict['label']
            
        # --- Priority 2: Domain Reputation List (Only applies if Priority 1 wasn't decisive) ---
        elif domain_root and domain_root in LOW_REPUTATION_DOMAINS:
            reputation = LOW_REPUTATION_DOMAINS[domain_root]
            verdict = reputation['verdict']
            label = reputation['label']
        
        # --- Final Compilation ---
        response_data.append({
            "url": url,
            "domain": domain_root,
            "verdict": verdict,
            "label": label 
        })
    
    print("[BACKEND] All checks complete. Sending final verdicts.")
    return response_data


# --- 4. Server Start ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)