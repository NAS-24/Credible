// content.js
console.log("Credible Content Script Loaded!");

// --- 1. CONFIGURATION ---
// 💥 FIX 1: Define the Base Host URL (must end with a slash for safety)
const BASE_HOST_URL = "https://credible-38kn.onrender.com/"; 
// 💥 FIX 2: Define the API Endpoint Path
const API_PATH = "api/check-credibility/"; 
const CACHED_LINKS = new Map(); 

// Function to extract the user's search query from the URL bar (e.g., from ?q=...)
function getUserSearchQuery() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get("q");
        return query ? decodeURIComponent(query.replace(/\+/g, " ")) : null;
    } catch (e) {
        console.error("Could not extract search query from URL:", e);
        return null;
    }
}

// --- 2. Main Execution Function ---
window.onload = function() {
    const userQuery = getUserSearchQuery();
    console.log(`User Query Extracted: ${userQuery || "N/A"}`);

    console.log("Page has loaded. Starting link extraction...");

    const linkElements = document.querySelectorAll('a:has(h3)'); 
    let searchResults = [];
    
    linkElements.forEach(link => {
        const url = link.href;
        if (url && url.startsWith("http")) {
            try {
                const domain = new URL(url).hostname;
                const uniqueKey = url;

                searchResults.push({ url: url, domain: domain });
                CACHED_LINKS.set(uniqueKey, link); 

            } catch (e) {
                // Ignore invalid URLs
            }
        }
    });

    console.log(`Found ${searchResults.length} potential search results.`);
    
    if (searchResults.length > 0) {
        sendDataToBackend(searchResults, userQuery);
    }
};

// --- 3. Communication Function (UPDATED FETCH) ---
async function sendDataToBackend(data, userQuery) {
    // Construct the full URL using the components
    const FULL_API_ENDPOINT = BASE_HOST_URL + API_PATH; 
    
    try {
        console.log(`[FRONTEND] Sending ${data.length} items to backend at ${FULL_API_ENDPOINT}...`);
        
        // Build the combined payload that matches the FastAPI Pydantic model
        const payload = {
            links: data,
            query: userQuery,
        };

        const response = await fetch(FULL_API_ENDPOINT, { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
             // This will catch the 404 if the path is wrong, or 503 if the server is asleep
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const verdicts = await response.json();
        
        console.log("-----------------------------------------");
        console.log(`[FRONTEND] SUCCESS! Received ${verdicts.length} verdicts.`);
        console.log("FULL VERDICTS ARRAY:", verdicts);
        
        injectVerdictsIntoPage(verdicts); 

    } catch (error) {
        console.error(
          "[FRONTEND] Error communicating with backend. Connection failed or HTTP status error.",
          error
        );
    }
}

// --- 4. RENDERING LOGIC (Phase 3) ---
function injectVerdictsIntoPage(verdicts) {
    let injectedCount = 0;

    verdicts.forEach(verdict => {
        const linkElement = CACHED_LINKS.get(verdict.url);
        
        if (linkElement && verdict.label) {
            
            // FIX: Using <bdi> to solve the text mirroring issue
            const tag = document.createElement("span");
            const bdiElement = document.createElement("bdi"); 
            bdiElement.textContent = verdict.label;
            tag.appendChild(bdiElement); 
            
            // --- Determine the CSS Class based on verdict status ---
            let tagClass = "tag-neutral"; 

            if (verdict.verdict.includes("Fact Checked CLAIM")) {
                tagClass = "tag-verified"; 
            } else if (verdict.verdict.includes("Satire") || verdict.verdict.includes("Humor")) {
                tagClass = "tag-satire";
            } else if (verdict.verdict.includes("Bias") || verdict.verdict.includes("Propaganda") || verdict.verdict.includes("Fake")) {
                tagClass = "tag-bad";
            }

            tag.className = `credible-tag ${tagClass}`;
            
            const injectionPoint = linkElement.querySelector("h3");
            
            if (injectionPoint) {
                injectionPoint.after(tag);
                injectedCount++;
            }
        }
    });
    console.log(`[FRONTEND] Injected ${injectedCount} credibility tags into the search results.`);
}
