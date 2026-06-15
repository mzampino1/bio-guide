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
    Test that a valid location string successfully returns a tuple of float coordinates
    and the raw location dictionary.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_OSM_SUCCESS
    
    lat, lng, raw_result = get_coordinates("Central Park")
    
    assert lat == 40.7851
    assert lng == -73.9682
    assert raw_result == MOCK_OSM_SUCCESS[0]
    mock_get.assert_called_once()


@patch('src.apis.geocoding.requests.get')
def test_get_coordinates_not_found(mock_get):
    """
    Test that an unrecognizable location returns (None, None, None) instead of throwing an IndexError.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = []
    
    lat, lng, raw_result = get_coordinates("NonExistentPlace12345")
    
    assert lat is None
    assert lng is None
    assert raw_result is None


@patch('src.apis.geocoding.requests.get')
def test_get_coordinates_api_error(mock_get):
    """
    Test that network failures or server errors are caught gracefully and return (None, None, None).
    """
    mock_get.return_value.raise_for_status.side_effect = HTTPError("Simulated 500 Server Error")
    
    lat, lng, raw_result = get_coordinates("Paris")

    # Assert
    assert lat is None
    assert lng is None
    assert raw_result is None