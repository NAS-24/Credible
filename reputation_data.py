# reputation_data.py

# A simple list of known low-reputation or satire domains for the MVP test.
# In a full app, this would be a large database managed by a service.

LOW_REPUTATION_DOMAINS = {
    "theonion.com": {
        "verdict": "Satire/Humor",
        "label": "Caution: Satire Source"
    },
    "infowars.com": {
        "verdict": "Conspiracy/Propaganda",
        "label": "Extreme Bias Detected"
    },
    "worldnewsdailyreport.com": {
        "verdict": "Known Fake News",
        "label": "False/Misleading Content"
    },
    # Existing test domain
    "example.com": {
        "verdict": "Test Domain",
        "label": "Test Code Complete"
    },
    # Famous/most visited low-reputation domains added (non-Indian)
    "babylonbee.com": {
        "verdict": "Satire/Humor",
        "label": "Caution: Satire Source"
    },
    "breitbart.com": {
        "verdict": "Extreme Bias/Propaganda",
        "label": "Extreme Bias Detected"
    },
    "dailycaller.com": {
        "verdict": "Strong Bias/Misleading",
        "label": "Significant Bias Detected"
    },
    "newspunch.com": {
        "verdict": "Conspiracy/Known Fake News",
        "label": "False/Misleading Content"
    },
    # New famous/most visited low-reputation Indian media domains added:
    "republicworld.com": {
        "verdict": "Extreme Bias/Sensationalism",
        "label": "Extreme Bias Detected (Godi Media)"
    },
    "timesnownews.com": {
        "verdict": "Extreme Bias/Sensationalism",
        "label": "Extreme Bias Detected (Godi Media)"
    },
    "zeenews.india.com": {
        "verdict": "Strong Bias/Misleading",
        "label": "Significant Bias Detected (Godi Media)"
    },
    "aajtak.in": {
        "verdict": "Sensationalism/Hyper-Partisan",
        "label": "Significant Bias Detected (Godi Media)"
    }
}

# In Phase 2.2, we will add the structure for the Fact-Check API results here.