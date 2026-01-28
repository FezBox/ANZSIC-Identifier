# API Documentation

## Overview

The ANZSIC Identifier API provides a simple RESTful endpoint to identify businesses and their recommended ANZSIC classifications based on physical addresses.

## Base URL

**Development**: `http://localhost:5000`
**Production**: `https://your-vercel-deployment.vercel.app`

## Authentication

Currently, no authentication is required for the API endpoint. The Google API key is managed server-side.

## Endpoints

### Identify Business

Identifies a business at a given address and returns its ANZSIC classification.

**Endpoint**: `POST /api/identify`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "address": "string (required)"
}
```

**Parameters**:
| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| address   | string | Yes      | Physical address of the business to identify     |

**Success Response (200 OK)**:
```json
{
  "source_intelligence": {
    "business_name": "string",
    "detected_type": "string",
    "address": "string",
    "raw_types": ["string"]
  },
  "recommended_classification": {
    "code": "string",
    "title": "string"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `source_intelligence.business_name` | string | Business name from Google Places |
| `source_intelligence.detected_type` | string | Primary business type detected |
| `source_intelligence.address` | string | Formatted address from Google Places |
| `source_intelligence.raw_types` | array | All business types detected by Google |
| `recommended_classification.code` | string | ANZSIC code |
| `recommended_classification.title` | string | ANZSIC classification title |

**Error Responses**:

**400 Bad Request** - Invalid or missing address
```json
{
  "error": "Address is required"
}
```

**400 Bad Request** - No business found
```json
{
  "error": "No business found at this address."
}
```

**500 Internal Server Error** - Server configuration issue
```json
{
  "error": "Server configuration error: Google API Key missing"
}
```

**500 Internal Server Error** - API request failure
```json
{
  "error": "API Request Failed: <error details>"
}
```

## Examples

### cURL

```bash
curl -X POST http://localhost:5000/api/identify \
  -H "Content-Type: application/json" \
  -d '{"address": "123 George St, Sydney"}'
```

### JavaScript (Fetch API)

```javascript
const response = await fetch('/api/identify', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    address: '123 George St, Sydney'
  })
});

const data = await response.json();
console.log(data);
```

### Python (requests)

```python
import requests

response = requests.post(
    'http://localhost:5000/api/identify',
    json={'address': '123 George St, Sydney'}
)

data = response.json()
print(data)
```

### Node.js (axios)

```javascript
const axios = require('axios');

const response = await axios.post('http://localhost:5000/api/identify', {
  address: '123 George St, Sydney'
});

console.log(response.data);
```

## Example Responses

### Restaurant

**Request**:
```json
{
  "address": "123 George St, Sydney"
}
```

**Response**:
```json
{
  "source_intelligence": {
    "business_name": "The Italian Place",
    "detected_type": "restaurant",
    "address": "123 George St, Sydney NSW 2000, Australia",
    "raw_types": ["restaurant", "food", "point_of_interest", "establishment"]
  },
  "recommended_classification": {
    "code": "4511",
    "title": "Cafes and Restaurants"
  }
}
```

### Gym/Fitness Center

**Request**:
```json
{
  "address": "456 Fitness Ave, Melbourne"
}
```

**Response**:
```json
{
  "source_intelligence": {
    "business_name": "FitLife Gym",
    "detected_type": "gym",
    "address": "456 Fitness Ave, Melbourne VIC 3000, Australia",
    "raw_types": ["gym", "health", "point_of_interest", "establishment"]
  },
  "recommended_classification": {
    "code": "9111",
    "title": "Health and Fitness Centres and Sports Centres"
  }
}
```

### Bank

**Request**:
```json
{
  "address": "789 Bank St, Brisbane"
}
```

**Response**:
```json
{
  "source_intelligence": {
    "business_name": "National Bank Branch",
    "detected_type": "bank",
    "address": "789 Bank St, Brisbane QLD 4000, Australia",
    "raw_types": ["bank", "finance", "point_of_interest", "establishment"]
  },
  "recommended_classification": {
    "code": "6221",
    "title": "Banking"
  }
}
```

## ANZSIC Code Mappings

The API maps Google Place types to ANZSIC codes using a predefined mapping. Here's a summary of major categories:

### Food & Beverage
- `4511` - Cafes and Restaurants
- `4512` - Takeaway Food Services
- `4520` - Pubs, Taverns and Bars
- `4123` - Liquor Retailing

### Retail
- `4110` - Supermarket and Grocery Stores
- `4251` - Clothing Retailing
- `4252` - Footwear Retailing
- `4221` - Electrical, Electronic and Gas Appliance Retailing
- `4211` - Furniture Retailing
- `4231` - Hardware and Building Supplies Retailing
- `4271` - Pharmaceutical, Cosmetic and Toiletry Goods Retailing

### Services
- `6221` - Banking
- `6932` - Accounting Services
- `6931` - Legal Services
- `6720` - Real Estate Services
- `7220` - Travel Agency and Tour Arrangement Services
- `9511` - Hairdressing and Beauty Services

### Health
- `8511` - General Practice Medical Services
- `8531` - Dental Services
- `8401` - Hospitals (Except Psychiatric Hospitals)
- `6970` - Veterinary Services

### Accommodation
- `4400` - Accommodation

### Automotive
- `3911` - Car Retailing (New)
- `6611` - Passenger Car Rental and Hiring
- `9419` - Other Automotive Repair and Maintenance
- `4000` - Fuel Retailing

For a complete list, see the `anzsic_map` in [anzsic_mapper.py](anzsic_mapper.py).

## Demo Mode

When no valid Google API key is configured, the API operates in demo mode:

- Returns mock data based on keywords in the address
- Business names include "(MOCK DATA)" suffix
- Useful for testing UI without API costs
- Automatically activates when `GOOGLE_API_KEY` is missing or set to `your_api_key_here`

## Rate Limiting

The API inherits Google Places API rate limits and quotas:

- **Free tier**: Limited requests per month
- **Paid tier**: Higher quotas based on billing

Monitor your usage in the [Google Cloud Console](https://console.cloud.google.com/).

## Error Handling

The API uses standard HTTP status codes:

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 400 | Bad Request (missing or invalid parameters) |
| 500 | Internal Server Error (API issues, configuration errors) |

All errors return JSON with an `error` field containing a description.

## Best Practices

1. **Validate addresses**: Ensure addresses are well-formed before submission
2. **Handle errors**: Always check response status and handle error cases
3. **Cache results**: Cache frequently queried addresses to reduce API costs
4. **Use specific addresses**: More specific addresses yield better results
5. **Test in demo mode**: Use demo mode during development to avoid API charges

## Limitations

- **One address per request**: Batch processing not yet supported
- **Google Places dependency**: Accuracy depends on Google Places data quality
- **Limited coverage**: Not all business types are mapped to ANZSIC codes
- **No pagination**: Returns only the first/most relevant result

## Future Enhancements

Planned improvements to the API:

- [ ] Batch address processing
- [ ] Authentication and API key management
- [ ] Rate limiting per client
- [ ] Response caching
- [ ] Confidence scores for classifications
- [ ] Alternative ANZSIC code suggestions
- [ ] Historical data and analytics

## Support

For API issues or questions, please refer to the main [README](README.md) or create an issue in the repository.
