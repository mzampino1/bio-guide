from apis.geocoding import get_coordinates, is_park
from apis.inat_requests import get_location_observations

def run_report_pipeline():
    """
    Interactively accepts a single location from the terminal, resolves its
    coordinates, and dynamically switches to a bounding box if a park is detected.
    """
    location = input("Enter a location for the biodiversity report: ").strip()
    
    if not location:
        print("Error: Location input cannot be empty.")
        return

    print(f"\n[1/2] Resolving location details for '{location}'...")
    lat, lng, raw_result = get_coordinates(location)
    
    if lat is None or lng is None:
        print(f"Error: Could not find map coordinates for '{location}'.")
        return
        
    print(f"Found Point: Lat {lat}, Lng {lng}")
    
    bbox = None
    if raw_result and is_park(raw_result):
        osm_bbox = raw_result.get("boundingbox")  # Format: [south, north, west, east]
        if osm_bbox and len(osm_bbox) == 4:
            print("-> Nature space detected! Constructing bounding box fields...")
            bbox = {
                "swlat": float(osm_bbox[0]),
                "nelat": float(osm_bbox[1]),
                "swlng": float(osm_bbox[2]),
                "nelng": float(osm_bbox[3])
            }

    print(f"\n[2/2] Gathering wildlife observations from iNaturalist...")
    
    # FIX 1: Removed 'per_page=200' 
    # FIX 2: Renamed 'raw_data' straight to 'observations' since it's already a list
    observations = get_location_observations(lat, lng, radius=5, bbox=bbox)
    
    if not observations:
        print("Error: No data could be retrieved from the iNaturalist network.")
        return
        
    print(f"Success: Retrieved {len(observations)} local observations!\n")
    
    print(f"Staging Biodiversity Report Data for '{location}'")
    
    # Iterate through the flattened list of observations
    for obs in observations:
        obs_id = obs.get("id")
        taxon_info = obs.get("taxon") or {}
        common_name = taxon_info.get("preferred_common_name", "Unknown")
        scientific_name = taxon_info.get("name", "Unknown")
        observed_on = obs.get("observed_on")
        
        print(f"Ready to Save - Obs #{obs_id}: {common_name} ({scientific_name}) - Seen: {observed_on}")
        
    print(f"{len(observations)} records successfully found.")

if __name__ == "__main__":
    run_report_pipeline()