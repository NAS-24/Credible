import asyncio
import httpx
from decouple import config
import json

# --- Configuration ---
# Uses the same setup as main.py to read your secret key
API_KEY = config('GOOGLE_FACT_CHECK_API_KEY', default='DUMMY_KEY_FOR_TESTING')
FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# --- Known Claim to Test ---
# This is a highly likely claim to have been fact-checked by a major outlet.
TEST_CLAIM = "drinking bleach cures coronavirus"
# Alternatively, use one that is False: "drinking bleach cures coronavirus"

async def test_fact_check_api():
    """
    Makes a single, asynchronous call to the Fact Check API 
    and prints the raw JSON response.
    """
    if API_KEY == 'DUMMY_KEY_FOR_TESTING':
        print("ERROR: API Key is still set to the dummy value.")
        print("Please ensure GOOGLE_FACT_CHECK_API_KEY is set in your .env file.")
        return

    print(f"Testing Fact Check API with query: '{TEST_CLAIM}'")
    
    # Use httpx's AsyncClient to make the request
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "query": TEST_CLAIM,
                "key": API_KEY,
                "pageSize": 1 # We only need one result for the test
            }
            
            response = await client.get(FACT_CHECK_URL, params=params, timeout=10.0)
            response.raise_for_status() # Will raise an error for 4xx/5xx status codes
            
            raw_data = response.json()

            print("\n=======================================================")
            print("✅ RAW API RESPONSE RECEIVED (200 OK)")
            print("=======================================================")
            
            # Print the entire structure, nicely formatted
            print(json.dumps(raw_data, indent=4))
            
            print("\n--- VERIFICATION CHECK ---")

            if raw_data.get('claims'):
                claim = raw_data['claims'][0]
                rating = claim['claimReview'][0].get('textualRating', 'N/A')
                publisher = claim['claimReview'][0]['publisher']['name']
                
                print(f"Claim Text: {claim.get('text', 'N/A')}")
                print(f"Rating Extracted: {rating}")
                print(f"Publisher Extracted: {publisher}")
                print("\nVerification successful. The structure matches the code's expectation.")
            else:
                print("No fact-check claim found for this specific query, but the connection is working.")
            
        except httpx.HTTPStatusError as e:
            print(f"\n❌ API COMMUNICATION FAILED: HTTP Status {e.response.status_code}")
            print("Details (often 403 Forbidden due to billing/restriction):", e.response.text)
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {e}")

# Run the asynchronous test function
if __name__ == "__main__":
    asyncio.run(test_fact_check_api())
