import requests
import json

url = "http://127.0.0.1:5001/api/identify"
# Use the address that likely yields "Autodesk" (user's screenshot says 19/15 William St)
# But user searched "45 William St" previously? Let's try 45 William St first as that's where the list came from.
payload = {"address": "15 William St, Melbourne"} 
headers = {"Content-Type": "application/json"}

print(f"Querying {url} for address: {payload['address']}...")
try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        
        candidates = []
        if data.get("status") == "multiple":
            candidates = data.get("candidates", [])
        elif data.get("status") == "single":
            candidates = [data.get("result")]
            
        print(f"Found {len(candidates)} candidates.")
        
        # Look for Autodesk or unknown items
        for c in candidates:
            name = c["source_intelligence"]["business_name"]
            ai_class = c.get("ai_classification")
            print(f"- {name}: AI Field = {ai_class}")
            
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
