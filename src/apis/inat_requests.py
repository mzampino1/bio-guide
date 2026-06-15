import requests
import time

BASE_URL = "https://api.inaturalist.org/v1/observations"

def get_location_observations(lat, lng, radius=5, per_page=3, bbox=None):
    """
    Fetches a small batch of recent observations from iNaturalist based on coordinates.
    """
    # iNaturalist API accepts parameters to filter the observation results
    params = {
        "lat": lat,
        "lng": lng,
        "per_page": per_page,
        "order": "desc",
        "order_by": "created_at",
    }

    if bbox:
        params.update({
            "swlat": bbox["swlat"],
            "swlng": bbox["swlng"],
            "nelat": bbox["nelat"],
            "nelng": bbox["nelng"],
        })
    else:
        params["radius"] = radius

    headers = {
        "User-Agent": "BioGuide/1.0 (https://github.com/mzampino1/bio-guide)"
    }
    
    try:
        print(f"Sending request to iNaturalist for coordinates: {lat}, {lng}...")
        response = requests.get(BASE_URL, params=params, headers=headers)
        
        # This will raise an exception if the API returns an error status code
        response.raise_for_status() 
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return None

# Testing
if __name__ == "__main__":
    # Test coordinates (Central Park, NY as a placeholder)
    TEST_LAT = 40.7851
    TEST_LNG = -73.9683
    
    data = get_location_observations(TEST_LAT, TEST_LNG)
    
    if data:
        results = data.get("results", [])
        print(f"\n--- Success! Retrieved {len(results)} observations ---")
        
        # Print out observations
        for result in results:
            print(f"ID: {result.get('id')}")
            print(f"Common Name: {result.get('taxon', {}).get('preferred_common_name', 'Unknown')}")
            print(f"Taxon Name: {result.get('taxon', {}).get('name', 'Unknown')}")
            print(f"Location: {result.get('location')}")
            print()
    else:
        print("\nNo data returned.")