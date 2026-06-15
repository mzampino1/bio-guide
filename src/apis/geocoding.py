import requests

OSM_URL = "https://nominatim.openstreetmap.org/search"

PARK_TYPES = {"park", "nature_reserve", "garden", "forest", "recreation_ground"}

def is_park(result):
    place_type = (result.get("type") or "").lower()
    place_class = (result.get("class") or "").lower()
    return place_type in PARK_TYPES or place_class in PARK_TYPES

def get_coordinates(location_string):
    """
    Converts a location string into (latitude, longitude)
    using the OpenStreetMap Nominatim API.
    """
    params = {
        "q": location_string,
        "format": "json",
        "limit": 1
    }
    
    headers = {
        "User-Agent": "BioGuide/1.0 (https://github.com/mzampino1/bio-guide)"
    }
    
    try:
        response = requests.get(OSM_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data:
            # OpenStreetMap returns coordinates as strings, convert them to floats
            lat = float(data[0]["lat"])
            lng = float(data[0]["lon"])
            return lat, lng
            
    except Exception as e:
        print(f"Geocoding error: {e}")
        
    return None, None