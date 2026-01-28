import unittest
from unittest.mock import MagicMock, patch
from anzsic_mapper import BusinessAnzsicLocator
import json

class TestAnzsicMapper(unittest.TestCase):
    def setUp(self):
        self.locator = BusinessAnzsicLocator("dummy_key")

    @patch('requests.post')
    def test_restaurant_mapping(self, mock_post):
        # Mocking a Google Places API response for a restaurant
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "places": [
                {
                    "displayName": {"text": "Test Cafe"},
                    "primaryType": "cafe",
                    "types": ["cafe", "restaurant", "food", "point_of_interest", "establishment"],
                    "formattedAddress": "123 Test St"
                }
            ]
        }
        mock_post.return_value = mock_response

        # Run the locator
        result = self.locator.get_business_details("123 Test St")

        # Verify API was called
        mock_post.assert_called_once()
        
        # Verify Mapped Output
        self.assertEqual(result["source_intelligence"]["detected_type"], "cafe")
        self.assertEqual(result["recommended_classification"]["code"], "4511")
        self.assertEqual(result["recommended_classification"]["title"], "Cafes and Restaurants")

    @patch('requests.post')
    def test_gym_mapping(self, mock_post):
        # Mocking a Gym response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "places": [
                {
                    "displayName": {"text": "Fit Gym"},
                    "primaryType": "gym",
                    "formattedAddress": "456 Fit Way"
                }
            ]
        }
        mock_post.return_value = mock_response

        result = self.locator.get_business_details("456 Fit Way")
        self.assertEqual(result["recommended_classification"]["code"], "9111")
        self.assertEqual(result["recommended_classification"]["title"], "Health and Fitness Centres and Sports Centres")

    @patch('requests.post')
    def test_no_results(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {} # Empty response
        mock_post.return_value = mock_response

        result = self.locator.get_business_details("Unknown Place")
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()
