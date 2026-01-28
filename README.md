# ANZSIC Identifier

A web application that automatically identifies businesses and recommends ANZSIC (Australian and New Zealand Standard Industrial Classification) codes based on physical addresses.

## Features

- **Address-based Classification**: Enter any business address to get its ANZSIC classification
- **Nearby Business Search**: Automatically detects businesses at generic addresses (addresses without a specific business name) and finds relevant businesses nearby (New)
- **Google Places Integration**: Leverages Google Places API (New) for accurate business identification
- **70+ Business Type Mappings**: Comprehensive mapping of Google Place types to ANZSIC codes
- **Demo Mode**: Test the application without an API key using mock data
- **Modern UI**: Clean, responsive interface built with Tailwind CSS
- **Data Flow Visualizer**: Interactive visualization showing how data flows through the system
- **RESTful API**: JSON API endpoint for programmatic access

## Live Demo

The application is deployed on Vercel and includes a demo mode for testing without a Google API key.

## Technology Stack

- **Backend**: Python 3.x, Flask
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **APIs**: Google Places API (New)
- **Deployment**: Vercel (serverless)
- **Testing**: Python unittest

## Prerequisites

- Python 3.7 or higher
- Google Cloud Platform account (for Google Places API key)
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "ANZSIC Identifier"
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

## Google Places API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Places API (New)**
4. Create credentials (API Key)
5. (Optional) Restrict the API key to your domain for security
6. Copy the API key to your `.env` file

## Usage

### Running Locally

1. **Start the Flask development server**
   ```bash
   python app.py
   ```

2. **Access the application**
   - Main interface: [http://localhost:5000](http://localhost:5000)
   - Visualizer demo: [http://localhost:5000/visualizer](http://localhost:5000/visualizer)

3. **Test the application**
   - Enter a business address (e.g., "123 George St, Sydney")
   - Click "Identify"
   - View the detected business type and recommended ANZSIC code

### Demo Mode

If no valid API key is configured, the application automatically runs in demo mode with mock data. This allows you to test the UI without API access.

### API Endpoint

**POST** `/api/identify`

**Request Body:**
```json
{
  "address": "123 George St, Sydney"
}
```

**Response:**
```json
{
  "source_intelligence": {
    "business_name": "Example Cafe",
    "detected_type": "cafe",
    "address": "123 George St, Sydney NSW 2000, Australia",
    "raw_types": ["cafe", "restaurant", "food", "point_of_interest"]
  },
  "recommended_classification": {
    "code": "4511",
    "title": "Cafes and Restaurants"
  }
}
```

**Error Response:**
```json
{
  "error": "No business found at this address."
}
```

## Testing

Run the test suite:
```bash
python -m pytest test_mapper.py
```

Or using unittest directly:
```bash
python test_mapper.py
```

## Deployment

### Vercel Deployment

The application is configured for Vercel deployment with [vercel.json](vercel.json).

1. **Install Vercel CLI** (if not already installed)
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

3. **Set environment variables** in Vercel dashboard
   - Add `GOOGLE_API_KEY` in Project Settings → Environment Variables

4. **Deploy to production**
   ```bash
   vercel --prod
   ```

### Other Platforms

The application can be deployed to any platform supporting Python/Flask:
- **Heroku**: Use Procfile with `web: gunicorn app:app`
- **AWS Elastic Beanstalk**: Package as Python application
- **Google Cloud Run**: Containerize with Docker
- **Azure App Service**: Deploy as Python web app

## Project Structure

```
ANZSIC Identifier/
├── app.py                 # Flask application entry point
├── anzsic_mapper.py       # Core business logic and ANZSIC mapping
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel deployment configuration
├── .env.example          # Environment variable template
├── .env                  # Environment variables (not in git)
├── test_mapper.py        # Unit tests
└── templates/
    ├── index.html        # Main application interface
    └── visualizer.html   # Data flow visualizer
```

## Supported Business Types

The application currently maps 70+ Google Place types to ANZSIC codes, including:

- **Food & Beverage**: Restaurants, cafes, bars, takeaway services
- **Retail**: Supermarkets, clothing stores, electronics, hardware
- **Services**: Banks, accounting, legal, real estate, travel agencies
- **Health**: Doctors, dentists, hospitals, veterinary care
- **Accommodation**: Hotels, motels, lodging
- **Automotive**: Car dealers, rentals, repairs, gas stations
- **Education**: Schools, universities
- **Other**: Libraries, postal services, emergency services

See [anzsic_mapper.py:12-72](anzsic_mapper.py#L12-L72) for the complete mapping.

## Extending the Mappings

To add new business type mappings, edit the `anzsic_map` dictionary in [anzsic_mapper.py](anzsic_mapper.py):

```python
self.anzsic_map = {
    "your_google_place_type": {
        "code": "1234",
        "title": "Your ANZSIC Classification Title"
    },
    # ... more mappings
}
```

## Limitations

- **Coverage**: Not all Google Place types are mapped to ANZSIC codes
- **Accuracy**: ANZSIC classification is based on Google's business categorization
- **API Costs**: Google Places API usage may incur charges beyond free tier
- **Address Quality**: Results depend on address accuracy and Google Places data quality

## Contributing

Contributions are welcome! Areas for improvement:

1. **Expand ANZSIC mappings**: Add more Google Place type to ANZSIC code mappings
2. **Improve classification logic**: Handle ambiguous cases better
3. **Add caching**: Cache API responses to reduce costs
4. **Batch processing**: Support multiple addresses at once
5. **Export functionality**: Export results to CSV/Excel

## License

[Add your license information here]

## Support

For issues and questions:
- Check existing GitHub Issues
- Create a new issue with detailed description
- Include sample addresses and error messages

## Credits

- ANZSIC codes based on the Australian Bureau of Statistics classification system
- Business data powered by Google Places API
- UI components styled with Tailwind CSS

## Changelog

### Version 2.0.0 (Major Release)
- **Official ANZSIC 2006 Dataset**: Upgraded internal database from ~70 mappings to the **Full Official ANZSIC 2006 Standard** (506 unique codes).
- **Hybrid AI Classification**:
    - **Dual Card UI**: Clearly separates "Verified/Official" matches from "AI Recommendations".
    - **Official Title Lookup**: AI predicts the code, but the system cross-references the official database to provide the *legal* industry title (e.g. `6310` -> "Internet Service Providers"), eliminating hallucinations.
- **Smart Caching**: Implemented in-memory caching for zero-latency lookups on repeated searches.
- **Batch AI Processing**: Optimizes API usage by batching multiple candidates into a single LLM call.
- **Performance**: Reduced API calls significantly through caching and batching strategies.

### Version 1.2.0
- **New Feature**: "Deep In-Building Search" - Fetches up to 20 businesses per location using advanced distance ranking, ensuring complete coverage of shopping centers and office blocks.
- **Architecture**: Complete rewrite of the frontend into a robust **Single Page Application (SPA)**.
- **UI/UX**: Implemented **Web Interface Guidelines** including:
    - Instant "Back" navigation (no API-re-fetch).
    - Stateful views (Search / List / Details).
    - Accessible focus states and semantic typography.
- **Visuals**: Premium "Inter" font, loading states, and result counters.

### Version 1.1.0
- **New Feature**: "Nearby Business Search" - Handles generic address searches (e.g., "123 Main St") by automatically searching for businesses within a 50m radius.
- **UI Update**: New selection list interface for when multiple businesses are found at the same location.
- **Fix**: Improved error handling for port conflicts on macOS.

### Version 1.0.0
- Initial release
- Google Places API integration
- 70+ business type mappings
- Demo mode support
- Vercel deployment configuration
