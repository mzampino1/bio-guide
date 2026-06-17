from unittest.mock import patch
from requests.exceptions import HTTPError
from src.apis.inat_requests import get_location_observations

# MOCK_API_RESPONSE represents a single page from iNaturalist
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
    Test that the function successfully loops, extracts the inner results,
    and returns a flat list of observations.
    """
    # Mock a successful single-page response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = MOCK_API_RESPONSE
    
    result = get_location_observations(40.7851, -73.9683)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["species_guess"] == "Monarch Butterfly"
    mock_get.assert_called_once()


@patch('src.apis.inat_requests.requests.get')
def test_get_location_observations_failure(mock_get):
    """
    Test that an API network error breaks the loop gracefully and returns whatever 
    was collected before the failure (or an empty list).
    """
    mock_get.return_value.status_code = 500
    mock_get.return_value.raise_for_status.side_effect = HTTPError("Server Error")
    
    result = get_location_observations(40.7851, -73.9683)
    
    assert result == []


@patch('src.apis.inat_requests.requests.get')
def test_get_location_observations_uses_radius_for_regular_locations(mock_get):
    """
    Non-park searches should keep the point + radius query path.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"results": []}  # Empty list breaks the loop instantly

    get_location_observations(40.7851, -73.9683, radius=2)

    _, kwargs = mock_get.call_args
    params = kwargs["params"]

    assert params["lat"] == 40.7851
    assert params["lng"] == -73.9683
    assert params["radius"] == 2
    assert "swlat" not in params


@patch('src.apis.inat_requests.requests.get')
def test_get_location_observations_uses_bbox_for_park_queries(mock_get):
    """
    Park searches should switch to a bounding-box query instead of a point radius.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"results": []}  # Empty list breaks the loop instantly

    bbox = {
        "swlat": 40.70,
        "swlng": -74.00,
        "nelat": 40.90,
        "nelng": -73.80,
    }

    get_location_observations(40.7851, -73.9683, bbox=bbox)

    _, kwargs = mock_get.call_args
    params = kwargs["params"]

    assert params["swlat"] == bbox["swlat"]
    assert params["swlng"] == bbox["swlng"]
    assert params["nelat"] == bbox["nelat"]
    assert params["nelng"] == bbox["nelng"]
    assert "radius" not in params


@patch('src.apis.inat_requests.time.sleep')  # Mock sleep so unit tests execute instantly
@patch('src.apis.inat_requests.requests.get')
def test_get_location_observations_pagination_limit(mock_get, mock_sleep):
    """
    Verify that pagination respects the max_observations ceiling and truncates cleanly.
    """
    # Build a mock page containing exactly 200 items
    fake_200_results = {"results": [{"id": i} for i in range(200)]}
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = fake_200_results

    # Request data with a hard ceiling of 250 records.
    # Page 1 fetches 200. Page 2 fetches another 200 (Total 400). Loop terminates and truncates to 250.
    result = get_location_observations(40.7851, -73.9683, max_observations=250)

    assert len(result) == 250
    assert mock_get.call_count == 2