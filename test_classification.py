import os
import time
from anzsic_mapper import BusinessAnzsicLocator
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # Use a dummy key if env var missing, but strict tests might fail if they need real API
    api_key = "test_key" 

locator = BusinessAnzsicLocator(api_key, gemini_key)

test_cases = [
    {"name": "McDonalds", "address": "123 Main St", "type": "fast_food_restaurant", "expected_method": "direct_map"},
    {"name": "AED Legal Centre", "address": "45 William St, Melbourne", "type": "lawyer", "expected_method": "direct_map"}, # Lawyer is in map now
    {"name": "Luggage Storage", "address": "45 William St", "type": "storage", "expected_method": "keyword_match"}, # 'Storage' probably not in direct map
    {"name": "Random Unclassified Business", "address": "45 William St", "type": "unknown", "expected_method": "ai_inferred_raw"} # Should trigger AI
]

# We Mock the AI request or purely test the logic flow?
# Better to test logic flow first.

print("--- Starting Classification Test ---")

# 1. Test Direct Map
print("\nTest 1: Direct Map (Cafe)")
res1 = locator._enrich_deterministic({"displayName": {"text": "My Cafe"}, "primaryType": "cafe", "formattedAddress": "1 St", "types": ["cafe"]})
print(f"Result: {res1['recommended_classification']['title']} | Method: {res1['source_intelligence']['match_method']}")

# 2. Test Keyword Match (if I add a specific kw to json)
# "Legal Services" is in JSON. "Legal" is in name.
print("\nTest 2: Keyword Match (Legal)")
# Mocking a type that is NOT in the direct map, but name has keyword
res2 = locator._enrich_deterministic({"displayName": {"text": "Smith Legal Services"}, "primaryType": "consultant", "formattedAddress": "1 St", "types": ["consultant"]})
print(f"Result: {res2['recommended_classification']['title']} | Method: {res2['source_intelligence']['match_method']}")

# 3. Test AI (Real Test with new Key)
print("\nTest 3: AI Inference (Real)")
# "Plumbing" is NOT in our local json, so it must go to AI.
res3 = locator._enrich_deterministic({"displayName": {"text": "Bob's Plumbing Services"}, "primaryType": "plumber", "formattedAddress": "123 Pipe Lane", "types": ["plumber"]})
print(f"Result: {res3['recommended_classification']['title']} | Code: {res3['recommended_classification']['code']} | Method: {res3['source_intelligence']['match_method']}")

import json
# 4. Test Batch Logic (Manual invocation)
print("\nTest 4: Batch AI Logic")
candidates = [
    {"name": "Bob's Plumbing", "type": "plumber"},
    {"name": "Alice's Electrical", "type": "electrician"}
]
# We need to manually call _batch_ai_classification to test it in isolation
results = locator._batch_ai_classification(candidates)
print(f"Batch Results: {json.dumps(results, indent=2)}")
