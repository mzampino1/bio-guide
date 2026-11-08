import sqlite3

from apis.geocoding import get_coordinates, is_park
from apis.inat_requests import get_location_observations
from database.db_insertion import reset_db, init_db, insert_data, DB_NAME
from processing.species_abundance import rank_species_with_grouping, rank_relative_abundance
from processing.observation_analytics import get_monthly_activity_trends, get_peak_month_for_species
from guide.pdf_generation import build_pdf_guide

def run_report_pipeline():
    """
    Interactively accepts a single location from the terminal, resolves its
    coordinates, and dynamically switches to a bounding box if a park is detected.
    """
    # Initialize SQLite database
    reset_db()
    init_db()
    
    location = input("Enter a location for the biodiversity report: ").strip()
    
    if not location:
        print("Error: Location input cannot be empty.")
        return

    print(f"\n[1/4] Resolving location details for '{location}'...")
    found_name, lat, lng, raw_result = get_coordinates(location)
    
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

    print(f"\n[2/4] Gathering wildlife observations from iNaturalist...")
    
    observations = get_location_observations(lat, lng, radius=5, bbox=bbox)
    
    if not observations:
        print("Error: No data could be retrieved from the iNaturalist network.")
        return
        
    print(f"Success: Retrieved {len(observations)} local observations!\n")
    print(f"Staging Biodiversity Report Data for {found_name}...")
    
    # Iterate through the flattened list of observations
    for obs in observations:
        # Extract coordinates so db_insertion.py can read obs.get("latitude")
        if "geojson" in obs and obs["geojson"]:
            # GeoJSON format is [longitude, latitude]
            coords = obs["geojson"].get("coordinates", [None, None])
            obs["longitude"] = coords[0]
            obs["latitude"] = coords[1]
        elif "location" in obs and obs["location"]:
            # Fallback if 'location' string "lat,lng" is present
            try:
                lat_str, lng_str = obs["location"].split(",")
                obs["latitude"] = float(lat_str)
                obs["longitude"] = float(lng_str)
            except ValueError:
                obs["latitude"] = None
                obs["longitude"] = None
        else:
            obs["latitude"] = None
            obs["longitude"] = None
        
    print(f"\n[3/4] Saving {len(observations)} records to database...")
    insert_data(observations)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Data extraction
    top_overall = rank_species_with_grouping(cursor, limit=35, group=None)
    top_plants = rank_species_with_grouping(cursor, limit=20, group="plants")
    top_animals = rank_species_with_grouping(cursor, limit=20, group="animals")
    
    relative_abundance = rank_relative_abundance(cursor, limit=35)
    monthly_trends = get_monthly_activity_trends(cursor)

    # PDF rendering
    print("\n\n[4/4] Building PDF guide...")
    build_pdf_guide(
        location=found_name,
        top_overall=top_overall,
        top_plants=top_plants,
        top_animals=top_animals,
        relative_abundance=relative_abundance,
        monthly_trends=monthly_trends,
        observations=observations,
        cursor=cursor
    )

    conn.close()

if __name__ == "__main__":
    run_report_pipeline()