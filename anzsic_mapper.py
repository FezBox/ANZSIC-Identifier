import requests
import json
import os

class BusinessAnzsicLocator:
    def __init__(self, google_api_key):
        self.api_key = google_api_key
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        self.nearby_url = "https://places.googleapis.com/v1/places:searchNearby"
        
        # Mapping of Google Place Types to ANZSIC Codes
        # This is a representative list and can be expanded.
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
                # If we found nearby candidates, return them as a list
                return {
                    "status": "multiple",
                    "candidates": [self._enrich_with_anzsic(c) for c in candidates]
                }
            else:
                # Standard single result (enriched)
                result = self._enrich_with_anzsic(place)
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
        
        result = self._enrich_with_anzsic(place)
        # Tag it as MOCK data for the UI to know (optional, but good for clarity)
        result["source_intelligence"]["business_name"] += " (MOCK DATA)"
        return result

    def _enrich_with_anzsic(self, place_data):
        """
        Maps the Google Place data to a recommended ANZSIC code.
        """
        # Strategy 1: Check Primary Type first
        primary_type = place_data.get("primaryType", "").lower()
        anzsic_info = self.anzsic_map.get(primary_type)
        
        # Strategy 2: If no match, check list of types
        if not anzsic_info:
            types = place_data.get("types", [])
            for t in types:
                t_lower = t.lower()
                if t_lower in self.anzsic_map:
                    anzsic_info = self.anzsic_map[t_lower]
                    break
        
        # Default fallback
        if not anzsic_info:
            anzsic_info = {"code": "Unknown", "title": "Classification Not Found"}

        return {
            "source_intelligence": {
                "business_name": place_data.get("displayName", {}).get("text", "Unknown Business"),
                "detected_type": primary_type if primary_type else "Unknown",
                "address": place_data.get("formattedAddress", "Unknown Address"),
                "raw_types": place_data.get("types", [])
            },
            "recommended_classification": anzsic_info
        }
