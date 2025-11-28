import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from urllib.parse import urlparse 
import os, sys
import httpx 
from decouple import config 
from pydantic import BaseModel # Used for LinkData/CredibilityPayload

# --- MVP DATA: Restore simple file import ---
# We assume reputation_data.py is in the same directory as main.py
try:
    from .reputation_data import LOW_REPUTATION_DOMAINS 
except ImportError:
    # Fallback for local run if running directly (python main.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from reputation_data import LOW_REPUTATION_DOMAINS 


# --- Pydantic Data Models (MUST MATCH FRONTEND) ---
class LinkData(BaseModel):
    url: str
    domain: str

class CredibilityPayload(BaseModel):
    links: List[LinkData]
    query: Optional[str] = None # The user's original search term


# --- 1. FastAPI App Initialization & Config ---
app = FastAPI(title="Credible MVP Backend")

# Get API Key securely from the .env file
API_KEY = config('GOOGLE_FACT_CHECK_API_KEY', default='YOUR_FALLBACK_KEY')
FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


# --- 2. CORS Configuration (CRITICAL) ---
origins = [
    "http://127.0.0.1:8888",
    "http://localhost:8888",
    "https://www.google.com",
    "https://*.google.com",    
    "chrome-extension://*",    
    "https://credible-38kn.onrender.com" # ADD RENDER URL FOR FULL SAFETY
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- 3. The Core MVP Logic (Combined Domain + API Check) ---
@app.post("/api/check-credibility")
async def check_credibility(payload: CredibilityPayload): 
    
    response_data = []
    fact_check_verdict = None
    
    # 1. CHECK TIER 2: Fact Check API (Run once using the user's search query)
    if payload.query and API_KEY != 'YOUR_FALLBACK_KEY':
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "query": payload.query, 
                    "key": API_KEY,
                    "pageSize": 1 
                }
                # Use a short timeout since this is a critical real-time check
                response = await client.get(FACT_CHECK_URL, params=params, timeout=5.0)
                response.raise_for_status() 
                data = response.json()
                
                if data.get('claims'):
                    claim_review = data['claims'][0]['claimReview'][0]
                    rating_text = claim_review.get('textualRating', 'RATED')
                    publisher = claim_review['publisher']['name']
                    
                    # Store the result as a Topic Warning
                    fact_check_verdict = {
                        "verdict": f"Fact Checked CLAIM: {rating_text}",
                        "label": f"CLAIM RATED {rating_text.upper()} by {publisher}",
                    }
                    print(f"[API CHECK] Match Found: {rating_text} by {publisher}")

        except httpx.HTTPStatusError as e:
            print(f"[API Error] Status {e.response.status_code} - Check API access/billing.")
        except Exception:
            pass # Fail gracefully if API connection times out or fails


    # 2. APPLY VERDICTS TO ALL LINKS
    for item in payload.links:
        url = item.url
        domain_root = None
        verdict = "Unassessed"
        label = "No Fact Check Found"
        
        try:
            domain_root = urlparse(url).netloc.replace('www.', '').strip()
        except Exception:
            pass 

        # --- Priority 1: Fact Check API Verdict (Apply to all links if found) ---
        if fact_check_verdict:
            verdict = fact_check_verdict['verdict']
            label = fact_check_verdict['label']
            
        # --- Priority 2: Domain Reputation List (Only if Priority 1 failed) ---
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


# --- 4. Server Start (Render ignores this block, but we keep it for local testing) ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=False)
