from unittest.mock import patch

from requests import HTTPError
from src.apis.geocoding import get_coordinates, is_park

# Mock data simulating a successful OpenStreetMap response for "Central Park"
MOCK_OSM_SUCCESS = [
    {
        "lat": "40.7851",
        "lon": "-73.9682",
        "display_name": "Central Park, New York, USA"
    }
]

def test_is_park_detects_park_like_results():
    assert is_park({"type": "park", "class": "leisure"}) is True
    assert is_park({"type": "nature_reserve", "class": "boundary"}) is True
    assert is_park({"type": "city", "class": "place"}) is False

@patch('src.apis.geocoding.requests.get')
def test_get_coordinates_success(mock_get):
    """
    Test that a valid location string successfully returns a tuple of float coordinates.
    """
    # Arrange: Configure the mock to pretend the API responded beautifully
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_OSM_SUCCESS
    
    # Act: Run the geocoding function
    lat, lng = get_coordinates("Central Park")
    
    # Assert: Verify the numbers were extracted and cast to floats correctly
    assert lat == 40.7851
    assert lng == -73.9682
    mock_get.assert_called_once()


@patch('src.apis.geocoding.requests.get')
def test_get_coordinates_not_found(mock_get):
    """
    Test that an unrecognizable location returns (None, None) instead of throwing an IndexError.
    """
    # Arrange: OpenStreetMap returns an empty list if nothing matches the query
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = []
    
    # Act
    lat, lng = get_coordinates("NonExistentPlace12345")
    
    # Assert
    assert lat is None
    assert lng is None


@patch('src.apis.geocoding.requests.get')
def test_get_coordinates_api_error(mock_get):
    """
    Test that network failures or server errors are caught gracefully and return (None, None).
    """
    # Arrange: Force the mock to RAISE an exception when raise_for_status() is called
    mock_get.return_value.raise_for_status.side_effect = HTTPError("Simulated 500 Server Error")
    
    # Act
    lat, lng = get_coordinates("Paris")

    # Assert
    assert lat is None
    assert lng is None