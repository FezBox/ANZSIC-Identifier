from flask import Flask, render_template, request, jsonify
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from anzsic_mapper import BusinessAnzsicLocator
import os
import re
import logging
from dotenv import load_dotenv
from html import escape

# Load environment variables from .env file
load_dotenv()

# Configure logging (StreamHandler only — Vercel has a read-only filesystem)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: Add security headers with Flask-Talisman
# Note: For development, we allow unsafe-inline for scripts/styles due to Tailwind CDN
# In production, you should use a proper CSP with local assets
talisman = Talisman(
    app,
    force_https=False,  # Set to True in production
    content_security_policy={
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com"],
        'img-src': ["'self'", "data:"]
    },
    content_security_policy_nonce_in=[],
)

# Rate limiting: Prevent API abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# Initialize the locator with the API keys
google_api_key = os.getenv("GOOGLE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
locator = BusinessAnzsicLocator(google_api_key, gemini_api_key)

# Input validation function
def validate_and_sanitize_address(address: str) -> str:
    """
    Validates and sanitizes the address input.

    Args:
        address: Raw address string from user input

    Returns:
        Sanitized address string

    Raises:
        ValueError: If address is invalid
    """
    if not address:
        raise ValueError("Address is required")

    # Remove leading/trailing whitespace
    address = address.strip()

    # Check length
    if len(address) < 3:
        raise ValueError("Address is too short")
    if len(address) > 500:
        raise ValueError("Address is too long (max 500 characters)")

    # Basic pattern validation - allow alphanumeric, spaces, commas, hyphens, periods
    if not re.match(r'^[\w\s,.\-#/]+$', address):
        raise ValueError("Address contains invalid characters")

    # Escape HTML to prevent XSS
    address = escape(address)

    logger.info(f"Validated address input: {address[:50]}...")
    return address

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/visualizer')
def visualizer():
    """Renders the visualizer demo page."""
    return render_template('visualizer.html')

@app.route('/api/identify', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter rate limit for API endpoint
def identify_business():
    """API endpoint to identify business and ANZSIC code from address."""
    try:
        data = request.get_json()

        if not data or 'address' not in data:
            logger.warning("API request missing address field")
            return jsonify({"error": "Address is required"}), 400

        # Validate and sanitize input
        try:
            address = validate_and_sanitize_address(data['address'])
        except ValueError as e:
            logger.warning(f"Invalid address input: {str(e)}")
            return jsonify({"error": str(e)}), 400

        # Check API key configuration
        if not google_api_key:
            logger.error("Google API Key not configured")
            return jsonify({"error": "Server configuration error: Google API Key missing"}), 500

        # Get business details
        logger.info(f"Processing request for address: {address[:50]}...")
        result = locator.get_business_details(address)

        if "error" in result:
            logger.warning(f"Business lookup failed: {result['error']}")
            return jsonify(result), 400

        logger.info("Successfully processed business identification request")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Unexpected error in identify_business: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    # Use environment variable for debug mode (default: False)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    if debug_mode:
        logger.warning("Running in DEBUG mode - do not use in production!")

    # Use port 5001 to avoid conflict with macOS AirPlay receiver on port 5000
    port = int(os.getenv('PORT', 5001))

    logger.info(f"Starting ANZSIC Identifier on port {port}")
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
