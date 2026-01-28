import requests
import json
import os

URL = "https://raw.githubusercontent.com/DamianMac/anzsic-codes/refs/heads/master/2006/all_classes.json"
OUTPUT_PATH = "data/anzsic_codes.json"

def main():
    print(f"Downloading ANZSIC data from {URL}...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
        raw_data = response.json()
        print(f"Downloaded {len(raw_data)} items.")
        
        # Transform
        transformed_data = []
        for item in raw_data:
            transformed_data.append({
                "code": item["class_code"],
                "title": item["class_title"]
            })
            
        # Save
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(transformed_data, f, indent=4)
            
        print(f"Successfully saved {len(transformed_data)} ANZSIC codes to {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
