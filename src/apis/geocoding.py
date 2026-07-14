import requests

OSM_URL = "https://nominatim.openstreetmap.org/search"

PARK_TYPES = {"park", "natural", "nature_reserve", "garden", "forest", "recreation_ground", "protected_area", "wilderness"}

def is_park(result):
    place_type = (result.get("type") or "").lower()
    place_class = (result.get("class") or "").lower()
    
    # Checks if any keyword from PARK_TYPES is a substring of the type or class
    return any(pt in place_type or pt in place_class for pt in PARK_TYPES)

def get_coordinates(location_string):
    """
    Converts a location string into (latitude, longitude, raw_result)
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
            found_name = data[0].get("name", "Unknown")
            lat = float(data[0]["lat"])
            lng = float(data[0]["lon"])
            # Return coordinates and the raw dictionary result
            return found_name, lat, lng, data[0]
            
    except Exception as e:
        print(f"Geocoding error: {e}")
        
    return 'Name of location unknown', None, None, None