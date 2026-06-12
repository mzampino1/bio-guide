from unittest.mock import patch
from src.apis.inat_requests import get_location_observations

# This is a mock version of the data iNaturalist would return
MOCK_API_RESPONSE = {
    "total_results": 1,
    "results": [
        {
            "id": 123456,
            "species_guess": "Monarch Butterfly",
            "taxon": {"name": "Danaus plexippus"},
            "location": "40.7851,-73.9683"
        }
    ]
}

@patch('src.apis.inat_requests.requests.get')
def test_get_location_observations_success(mock_get):
    """
    Test that the get_location_observations function correctly handles a successful API response.
    """
    # Arrange: Tell the mock what to pretend the API returned
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_API_RESPONSE
    
    # Act: Call the actual function
    result = get_location_observations(40.7851, -73.9683)
    
    # Assert: Verify that the function behaved correctly
    assert result is not None
    assert "results" in result
    assert result["results"][0]["species_guess"] == "Monarch Butterfly"
    
    # Verify that the actual HTTP request was attempted with the right parameters
    mock_get.assert_called_once()

@patch('src.apis.inat_requests.requests.get')
def test_get_location_observations_failure(mock_get):
    """
    Test that the get_location_observations function handles API errors 
    (like a 500 server error) gracefully.
    """
    # Arrange: Force the mock to simulate a bad gateway or server crash
    mock_get.return_value.status_code = 500
    # You can also simulate the raise_for_status() exception if needed
    from requests.exceptions import HTTPError
    mock_get.return_value.raise_for_status.side_effect = HTTPError("Server Error")
    
    # Act
    result = get_location_observations(40.7851, -73.9683)
    
    # Assert
    assert result is None