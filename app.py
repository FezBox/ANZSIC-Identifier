from flask import Flask, render_template, request, jsonify
from anzsic_mapper import BusinessAnzsicLocator
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize the locator with the API keys
google_api_key = os.getenv("GOOGLE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
locator = BusinessAnzsicLocator(google_api_key, gemini_api_key)

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/visualizer')
def visualizer():
    """Renders the visualizer demo page."""
    return render_template('visualizer.html')

@app.route('/api/identify', methods=['POST'])
def identify_business():
    """API endpoint to identify business and ANZSIC code from address."""
    data = request.get_json()
    
    if not data or 'address' not in data:
        return jsonify({"error": "Address is required"}), 400
        
    address = data['address']
    
    if not google_api_key:
        return jsonify({"error": "Server configuration error: Google API Key missing"}), 500

    result = locator.get_business_details(address)
    
    if "error" in result:
        # Determine status code based on error type if necessary, defaulting to 400 or 500
        return jsonify(result), 400 
        
    return jsonify(result)

if __name__ == '__main__':
    # Use port 5001 to avoid conflict with macOS AirPlay receiver on port 5000
    app.run(debug=True, port=5001)
