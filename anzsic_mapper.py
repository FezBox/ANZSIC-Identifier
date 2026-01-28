import requests
import json
import os

class BusinessAnzsicLocator:
    def __init__(self, google_api_key, gemini_api_key=None):
        self.api_key = google_api_key
        self.gemini_api_key = gemini_api_key
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        self.nearby_url = "https://places.googleapis.com/v1/places:searchNearby"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
        
        # Simple in-memory cache for AI results to save costs and speed up
        # Format: { "Business Name|Address": { "code": "1234", "title": "Title" } }
        self.ai_cache = {}

        # Load enhanced ANZSIC codes from JSON
        self.anzsic_codes = []
        try:
            json_path = os.path.join(os.path.dirname(__file__), "data", "anzsic_codes.json")
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    self.anzsic_codes = json.load(f)
                print(f"Loaded {len(self.anzsic_codes)} ANZSIC codes from database.")
            else:
                print("WARNING: anzsic_codes.json not found. Keyword matching will be limited.")
        except Exception as e:
            print(f"Error loading ANZSIC JSON: {e}")

        # Mapping of Google Place Types to ANZSIC Codes (Fast Tier 1)
        self.anzsic_map = {
            # Food & Beverage
            "cafe": {"code": "4511", "title": "Cafes and Restaurants"},
            "restaurant": {"code": "4511", "title": "Cafes and Restaurants"},
            "bar": {"code": "4520", "title": "Pubs, Taverns and Bars"},
            "bakery": {"code": "1172", "title": "Bakery Product Manufacturing (Non-factory based)"},
            "meal_takeaway": {"code": "4512", "title": "Takeaway Food Services"},
            
            # Retail
            "clothing_store": {"code": "4251", "title": "Clothing Retailing"},
            "shoe_store": {"code": "4252", "title": "Footwear Retailing"},
            "supermarket": {"code": "4110", "title": "Supermarket and Grocery Stores"},
            "grocery_store": {"code": "4110", "title": "Supermarket and Grocery Stores"},
            "convenience_store": {"code": "4110", "title": "Supermarket and Grocery Stores"},
            "furniture_store": {"code": "4211", "title": "Furniture Retailing"},
            "hardware_store": {"code": "4231", "title": "Hardware and Building Supplies Retailing"},
            "electronics_store": {"code": "4221", "title": "Electrical, Electronic and Gas Appliance Retailing"},
            "book_store": {"code": "4244", "title": "Newspaper and Book Retailing"},
            "florist": {"code": "4274", "title": "Flower Retailing"},
            "pharmacy": {"code": "4271", "title": "Pharmaceutical, Cosmetic and Toiletry Goods Retailing"},
            "drugstore": {"code": "4271", "title": "Pharmaceutical, Cosmetic and Toiletry Goods Retailing"},
            
            # Services
            "hair_salon": {"code": "9511", "title": "Hairdressing and Beauty Services"},
            "beauty_salon": {"code": "9511", "title": "Hairdressing and Beauty Services"},
            "real_estate_agency": {"code": "6720", "title": "Real Estate Services"},
            "travel_agency": {"code": "7220", "title": "Travel Agency and Tour Arrangement Services"},
            "lawyer": {"code": "6931", "title": "Legal Services"},
            "accounting": {"code": "6932", "title": "Accounting Services"},
            "bank": {"code": "6221", "title": "Banking"},
            "gym": {"code": "9111", "title": "Health and Fitness Centres and Gymnasia"},
            "laundry": {"code": "9531", "title": "Laundry and Dry-Cleaning Services"},
            
            # Health
            "doctor": {"code": "8511", "title": "General Practice Medical Services"},
            "dentist": {"code": "8531", "title": "Dental Services"},
            "hospital": {"code": "8401", "title": "Hospitals (Except Psychiatric Hospitals)"},
            "veterinary_care": {"code": "6970", "title": "Veterinary Services"},
            
            # Accommodation
            "hotel": {"code": "4400", "title": "Accommodation"},
            "motel": {"code": "4400", "title": "Accommodation"},
            "lodging": {"code": "4400", "title": "Accommodation"},
            
            # Automotive
            "car_dealer": {"code": "3911", "title": "Car Retailing (New)"},
            "car_rental": {"code": "6611", "title": "Passenger Car Rental and Hiring"},
            "car_repair": {"code": "9419", "title": "Other Automotive Repair and Maintenance"},
            "gas_station": {"code": "4000", "title": "Fuel Retailing"},
            
            # Education
            "school": {"code": "8023", "title": "Primary Education"}, # Simplified
            "university": {"code": "8102", "title": "Higher Education"},
            
            # Other
            "library": {"code": "6010", "title": "Libraries and Archives"},
            "post_office": {"code": "5101", "title": "Postal Services"},
            "police": {"code": "7712", "title": "Police Services"},
            "fire_station": {"code": "7713", "title": "Fire Protection and Other Emergency Services"}
        }

    def _batch_ai_classification(self, candidates):
        """
        Sends a single batch request to Gemini to classify multiple businesses.
        Includes Caching to minimize API calls.
        """
        if not self.gemini_api_key:
            return {}

        batch_results = {}
        to_process = []
        
        # 1. Check Cache
        for c in candidates:
            cache_key = f"{c['name']}|{c['address']}"
            if cache_key in self.ai_cache:
                print(f"Cache hit for: {c['name']}")
                batch_results[c['name']] = self.ai_cache[cache_key]
            else:
                to_process.append(c)
        
        if not to_process:
            return batch_results

        # 2. Process missing items
        items_str = ""
        for c in to_process:
             items_str += f"- Name: {c['name']}, Type: {c['type']}\n"
             
        prompt = f"""
        You are an expert ANZSIC classifier. Analyze the following list of businesses and assign the most appropriate 4-digit ANZSIC 2006 code AND the official ANZSIC Title to each.
        
        List:
        {items_str}
        
        You MUST return the result as a strict JSON object where keys are the specific Business Names provided and values are objects containing "code" and "title".
        
        CRITICAL: The "title" field MUST be the official ANZSIC industry title corresponding to the code. Do not leave it empty.
        
        Example format:
        {{
            "Business A": {{ "code": "1234", "title": "Software Publishing" }},
            "Business B": {{ "code": "5678", "title": "Plumbing Services" }}
        }}
        
        Do not include markdown formatting like ```json. Return only the raw JSON string. If you cannot determine a code, use "Unknown".
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        url = f"{self.gemini_url}?key={self.gemini_api_key}"
        
        try:
            response = requests.post(url, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                try:
                    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    clean_text = text.replace("```json", "").replace("```", "").strip()
                    
                    api_results = json.loads(clean_text)
                    
                    # Merge and Cache
                    for name, info in api_results.items():
                        # Validate Title - If missing, fallback to the business type from input if possible, or generic
                        final_title = info.get("title")
                        if not final_title or final_title == "AI Classified Industry":
                             # Try to derive a better fallback from our input "type" if possible, but here we just enforce non-empty
                             final_title = "Industry Classification" 
                        
                        info["title"] = final_title
                        
                        # Update Batch Results
                        batch_results[name] = info 
                        
                        # Update Cache (Find address for key)
                        for c in to_process:
                            if c['name'] == name:
                                cache_key = f"{name}|{c['address']}"
                                self.ai_cache[cache_key] = info
                                break
                                
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    print(f"Batch Parsing Failed: {e}")
                    print(f"Raw: {text}")
            else:
                print(f"AI Batch Error: {response.status_code} - {response.text}")
        except Exception as e:
             print(f"Batch Request Failed: {e}")
             
        return batch_results


        # Mapping of Google Place Types to ANZSIC Codes (Fast Tier 1)
        self.anzsic_map = {
            # Food & Beverage
            "restaurant": {"code": "4511", "title": "Cafes and Restaurants"},
            "cafe": {"code": "4511", "title": "Cafes and Restaurants"},
            "coffee_shop": {"code": "4511", "title": "Cafes and Restaurants"},
            "fast_food_restaurant": {"code": "4512", "title": "Takeaway Food Services"},
            "bar": {"code": "4520", "title": "Pubs, Taverns and Bars"},
            "liquor_store": {"code": "4123", "title": "Liquor Retailing"},
            "bakery": {"code": "1172", "title": "Bakery Product Manufacturing (Non-factory based)"}, # Or Retail
            
            # Retail
            "supermarket": {"code": "4110", "title": "Supermarket and Grocery Stores"},
            "grocery_store": {"code": "4110", "title": "Supermarket and Grocery Stores"},
            "convenience_store": {"code": "4110", "title": "Supermarket and Grocery Stores"},
            "clothing_store": {"code": "4251", "title": "Clothing Retailing"},
            "shoe_store": {"code": "4252", "title": "Footwear Retailing"},
            "electronics_store": {"code": "4221", "title": "Electrical, Electronic and Gas Appliance Retailing"},
            "furniture_store": {"code": "4211", "title": "Furniture Retailing"},
            "hardware_store": {"code": "4231", "title": "Hardware and Building Supplies Retailing"},
            "pharmacy": {"code": "4271", "title": "Pharmaceutical, Cosmetic and Toiletry Goods Retailing"},
            "drugstore": {"code": "4271", "title": "Pharmaceutical, Cosmetic and Toiletry Goods Retailing"},
            "florist": {"code": "4274", "title": "Flower Retailing"},
            
            # Services
            "bank": {"code": "6221", "title": "Banking"},
            "atm": {"code": "6221", "title": "Banking"},
            "accounting": {"code": "6932", "title": "Accounting Services"},
            "lawyer": {"code": "6931", "title": "Legal Services"},
            "real_estate_agency": {"code": "6720", "title": "Real Estate Services"},
            "travel_agency": {"code": "7220", "title": "Travel Agency and Tour Arrangement Services"},
            "hair_care": {"code": "9511", "title": "Hairdressing and Beauty Services"},
            "gym": {"code": "9111", "title": "Health and Fitness Centres and Sports Centres"},
            "laundry": {"code": "9531", "title": "Laundry and Dry-Cleaning Services"},
            
            # Health
            "doctor": {"code": "8511", "title": "General Practice Medical Services"},
            "dentist": {"code": "8531", "title": "Dental Services"},
            "hospital": {"code": "8401", "title": "Hospitals (Except Psychiatric Hospitals)"},
            "veterinary_care": {"code": "6970", "title": "Veterinary Services"},
            
            # Accommodation
            "hotel": {"code": "4400", "title": "Accommodation"},
            "motel": {"code": "4400", "title": "Accommodation"},
            "lodging": {"code": "4400", "title": "Accommodation"},
            
            # Automotive
            "car_dealer": {"code": "3911", "title": "Car Retailing (New)"},
            "car_rental": {"code": "6611", "title": "Passenger Car Rental and Hiring"},
            "car_repair": {"code": "9419", "title": "Other Automotive Repair and Maintenance"},
            "gas_station": {"code": "4000", "title": "Fuel Retailing"},
            
            # Education
            "school": {"code": "8023", "title": "Primary Education"}, # Simplified
            "university": {"code": "8102", "title": "Higher Education"},
            
            # Other
            "library": {"code": "6010", "title": "Libraries and Archives"},
            "post_office": {"code": "5101", "title": "Postal Services"},
            "police": {"code": "7712", "title": "Police Services"},
            "fire_station": {"code": "7713", "title": "Fire Protection and Other Emergency Services"}
        }

    def get_business_details(self, address):
        """
        Queries Google Places API to find the business at the address.
        """
        # DEMO MODE CHECK
        # If no valid key is provided, we return mock data so the user can test the UI.
        if not self.api_key or self.api_key == "your_api_key_here":
            print("WARNING: No valid API Key found. Using DEMO/MOCK mode.")
            return self._get_mock_response(address)

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # Requesting display name, primary type, multiple types, address AND location
            "X-Goog-FieldMask": "places.displayName,places.primaryType,places.types,places.formattedAddress,places.location"
        }
        
        payload = {
            "textQuery": address,
            "maxResultCount": 1
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status() # Raise exception for 4xx/5xx errors
            
            data = response.json()
            
            if not data.get("places"):
                return {"error": "No business found at this address."}
                
            place = data["places"][0]

            # CHECK FOR GENERIC ADDRESS
            primary_type = place.get("primaryType")
            generic_types = {"street_address", "subpremise", "premise", "route", "postal_code", "locality", "political"}
            is_generic = (primary_type is None) or (primary_type in generic_types)
            
            candidates = []
            
            if is_generic and "location" in place:
                print(f"Generic address result detected ({primary_type}). Searching nearby...")
                lat = place["location"]["latitude"]
                lng = place["location"]["longitude"]
                candidates = self._search_nearby(lat, lng)

            if candidates:
                # 1. Deterministic Enrichment (Fast)
                enriched_results = [self._enrich_deterministic(c) for c in candidates]
                
                # 2. Identify candidates needing AI
                ai_candidates = []
                for i, res in enumerate(enriched_results):
                    if res["source_intelligence"]["match_method"] == "failed":
                        ai_candidates.append({
                            "index": i,
                            "name": res["source_intelligence"]["business_name"],
                            "address": res["source_intelligence"]["address"],
                            "type": res["source_intelligence"]["detected_type"]
                        })
                
                # 3. Batch AI Classification (One HTTP Call + Caching)
                if ai_candidates:
                    print(f"Batch processing {len(ai_candidates)} businesses via AI...")
                    ai_results = self._batch_ai_classification(ai_candidates)
                    
                    # 4. Merge results
                    for item in ai_candidates:
                        idx = item["index"]
                        # ai_results is now a dict of {name: {"code": "...", "title": "..."}} OR just {name: "code"}
                        ai_info = ai_results.get(item["name"]) 
                        
                        if ai_info:
                            code = "Unknown"
                            title = "AI Classified Industry"
                            
                            if isinstance(ai_info, dict):
                                code = ai_info.get("code", "Unknown")
                                title_from_ai = ai_info.get("title", "AI Classified Industry")
                            elif isinstance(ai_info, str):
                                code = ai_info
                                title_from_ai = "AI Classified Industry"
                            
                            if code != "Unknown":
                                # 1. Try to find OFFICIAL title in local DB first (Source of Truth)
                                found_in_db = False
                                for db_item in self.anzsic_codes:
                                    if db_item["code"] == str(code):
                                        title = db_item["title"]
                                        found_in_db = True
                                        break
                                
                                # 2. If not in DB, use the title AI gave us
                                if not found_in_db and isinstance(ai_info, dict):
                                     title = title_from_ai

                                # STORE SEPARATELY.
                                enriched_results[idx]["ai_classification"] = {
                                    "code": code,
                                    "title": title
                                }

                return {
                    "status": "multiple",
                    "candidates": enriched_results
                }
            else:
                # Single result flow
                result = self._enrich_deterministic(place)
                # Ensure structure exists
                result["ai_classification"] = None
                
                if result["source_intelligence"]["match_method"] == "failed":
                     # Fallback to AI (Use Batch Logic for Consistency & Caching)
                     # We wrap this single item as a "candidate"
                     candidate = {
                        "name": result["source_intelligence"]["business_name"],
                        "address": result["source_intelligence"]["address"],
                        "type": result["source_intelligence"]["detected_type"]
                     }
                     
                     
                     
                     # Re-use the batch method (which handles Caching & Object parsing)
                     ai_results = self._batch_ai_classification([candidate])
                     ai_info = ai_results.get(candidate["name"])
                     
                     if ai_info:
                        code = "Unknown"
                        title = "AI Classified Industry"
                        
                        if isinstance(ai_info, dict):
                            code = ai_info.get("code", "Unknown")
                            title_from_ai = ai_info.get("title", "AI Classified Industry")
                        elif isinstance(ai_info, str):
                            code = ai_info
                            title_from_ai = "AI Classified Industry"
                            
                        if code != "Unknown":
                            # 1. Try to find OFFICIAL title in local DB first
                            found_in_db = False
                            for db_item in self.anzsic_codes:
                                if db_item["code"] == str(code):
                                    title = db_item["title"]
                                    found_in_db = True
                                    break
                            
                            # 2. If not in DB, use title from AI
                            if not found_in_db and isinstance(ai_info, dict):
                                    title = title_from_ai

                            result["ai_classification"] = {
                                "code": code,
                                "title": title
                            }

                return {"status": "single", "result": result}
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API Request Failed: {str(e)}"}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

    def _search_nearby(self, lat, lng):
        """
        Searches for businesses within a small radius of the coordinate.
        """
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.primaryType,places.types,places.formattedAddress"
        }
        
        payload = {
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "radius": 50.0 # 50 meters
                }
            },
            "maxResultCount": 20,
            "rankPreference": "DISTANCE"
        }
        
        try:
            response = requests.post(self.nearby_url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                places = data.get("places", [])
                
                # Filter out generic places from the nearby results
                valid_places = []
                generic_types = {"street_address", "subpremise", "premise", "route", "postal_code", "locality", "political"}
                
                for p in places:
                    p_type = p.get("primaryType")
                    if p_type and p_type not in generic_types:
                        valid_places.append(p)
                        
                return valid_places
        except Exception as e:
            print(f"Nearby search failed: {e}")
            
        return []

    def _get_mock_response(self, address):
        """
        Returns a mock response for testing purposes based on keywords in the address.
        """
        address_lower = address.lower()
        
        if "gym" in address_lower or "fitness" in address_lower:
             place = {"displayName": {"text": "Demo Fitness Centre"}, "primaryType": "gym", "types": ["gym", "health", "point_of_interest"], "formattedAddress": address}
        elif "bank" in address_lower:
             place = {"displayName": {"text": "Demo Bank Branch"}, "primaryType": "bank", "types": ["bank", "finance"], "formattedAddress": address}
        elif "school" in address_lower:
             place = {"displayName": {"text": "Demo Primary School"}, "primaryType": "school", "types": ["school", "education"], "formattedAddress": address}
        elif "hotel" in address_lower:
             place = {"displayName": {"text": "The Grand Demo Hotel"}, "primaryType": "hotel", "types": ["hotel", "accommodation"], "formattedAddress": address}
        elif "doctor" in address_lower or "medical" in address_lower:
             place = {"displayName": {"text": "Demo Medical Centre"}, "primaryType": "doctor", "types": ["doctor", "health"], "formattedAddress": address}
        else:
            # Default to a Cafe
            place = {
                "displayName": {"text": "The Demo Cafe"},
                "primaryType": "cafe",
                "types": ["cafe", "restaurant", "food", "point_of_interest", "establishment"],
                "formattedAddress": address
            }
        
        result = self._enrich_deterministic(place) # Changed from _enrich_with_anzsic
        # Tag it as MOCK data for the UI to know (optional, but good for clarity)
        result["source_intelligence"]["business_name"] += " (MOCK DATA)"
        return result

    def _enrich_deterministic(self, place_data):
        """
        Maps the Google Place data to a recommended ANZSIC code using Tiers 1 & 2 only (No AI).
        """
        business_name = place_data.get("displayName", {}).get("text", "Unknown Business")
        primary_type = place_data.get("primaryType", "").lower()
        address = place_data.get("formattedAddress", "Unknown Address")
        types = place_data.get("types", [])
        
        match_method = "unknown"
        anzsic_info = None

        # --- TIER 1: Direct Mapping (Fast, Exact) ---
        if primary_type:
            anzsic_info = self.anzsic_map.get(primary_type)
            if anzsic_info:
                match_method = "direct_map"
        
        if not anzsic_info:
            for t in types:
                t_lower = t.lower()
                if t_lower in self.anzsic_map:
                    anzsic_info = self.anzsic_map[t_lower]
                    match_method = "direct_map_fallback"
                    break

        # --- TIER 2: Keyword Matching (Broad, Local DB) ---
        if not anzsic_info and self.anzsic_codes:
            name_lower = business_name.lower()
            best_match = None
            
            for item in self.anzsic_codes:
                title_lower = item["title"].lower()
                stopwords = {"and", "or", "the", "services", "retailing", "manufacturing", "other", "not", "elsewhere", "classified", "n.e.c.", "goods", "shop", "store", "centre"}
                title_words = [w for w in title_lower.split() if w not in stopwords and len(w) > 3]
                
                for word in title_words:
                    if word in name_lower:
                        # Found a match!
                        best_match = item
                        break
                if best_match:
                    break
            
            if best_match:
                anzsic_info = best_match
                match_method = "keyword_match"

        # --- Fallback ---
        if not anzsic_info:
            anzsic_info = {"code": "Unknown", "title": "Classification Not Found"}
            match_method = "failed" # This triggers the AI batch later

        return {
            "source_intelligence": {
                "business_name": business_name,
                "detected_type": primary_type if primary_type else "Unknown",
                "address": address,
                "raw_types": types,
                "match_method": match_method 
            },
            "recommended_classification": anzsic_info,
            "ai_classification": None # Default to None, filled later if needed
        }

    def _batch_ai_classification(self, candidates):
        """
        Sends a single batch request to Gemini to classify multiple businesses.
        """
        if not self.gemini_api_key:
            return {}

        # Construct the batch prompt
        # We start with specific instructions including example of desired JSON format.
        # JSON output Mode is supported by Gemini Flash but raw text parsing works if simple.
        
        items_str = ""
        for c in candidates:
             items_str += f"- Name: {c['name']}, Type: {c['type']}\n"
             
        prompt = f"""
        You are an expert ANZSIC classifier. Analyze the following list of businesses and assign the most appropriate 4-digit ANZSIC code to each.
        
        List:
        {items_str}
        
        You MUST return the result as a strict JSON object where keys are the specific Business Names provided and values are the 4-digit code strings.
        Example format:
        {{
            "Business A": "1234",
            "Business B": "5678"
        }}
        
        Do not include markdown formatting like ```json. Return only the raw JSON string. If you cannot determine a code, use "9999".
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        url = f"{self.gemini_url}?key={self.gemini_api_key}"
        
        try:
            response = requests.post(url, json=payload, timeout=15) # Longer timeout for batch
            if response.status_code == 200:
                result = response.json()
                try:
                    text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    clean_text = text.replace("```json", "").replace("```", "").strip()
                    
                    batch_results = json.loads(clean_text)
                    return batch_results
                except (KeyError, IndexError, json.JSONDecodeError) as e:
                    print(f"Batch Parsing Failed: {e}")
                    print(f"Raw: {text}")
            else:
                print(f"AI Batch Error: {response.status_code} - {response.text}")
        except Exception as e:
             print(f"Batch Request Failed: {e}")
             
        return {}
