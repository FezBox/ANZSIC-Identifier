import requests
import json

url = "http://127.0.0.1:5001/api/identify"
payload = {"address": "45 William St, Melbourne"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("JSON Response:", json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print("Failed to decode JSON. Response content:")
        print(response.text[:500]) # Print first 500 chars to see the HTML error
except Exception as e:
    print(f"Request failed: {e}")
