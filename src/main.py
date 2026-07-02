import sqlite3

from apis.geocoding import get_coordinates, is_park
from apis.inat_requests import get_location_observations
from database.db_insertion import reset_db, init_db, insert_data
from processing.species_abundance import rank_species, rank_relative_abundance
from processing.observation_analytics import get_monthly_activity_trends, find_biodiversity_hotspots, get_peak_month_for_species

DB_NAME = r"tmp\bioguide.db"

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

    print(f"\n[1/3] Resolving location details for '{location}'...")
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

    print(f"\n[2/3] Gathering wildlife observations from iNaturalist...")
    
    observations = get_location_observations(lat, lng, radius=5, bbox=bbox)
    
    if not observations:
        print("Error: No data could be retrieved from the iNaturalist network.")
        return
        
    print(f"Success: Retrieved {len(observations)} local observations!\n")
    print(f"Staging Biodiversity Report Data for '{location}'")
    
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

        obs_id = obs.get("id")
        taxon_info = obs.get("taxon") or {}
        common_name = taxon_info.get("preferred_common_name", "Unknown")
        scientific_name = taxon_info.get("name", "Unknown")
        observed_on = obs.get("time_observed_at", obs.get("observed_on"))
        
        print(f"Staged - Obs #{obs_id}: {common_name} ({scientific_name}) - Seen: {observed_on}")
        
    print(f"\n[3/3] Saving {len(observations)} records to database...")
    
    # 2. Pass the enriched list to your database script
    insert_data(observations)
    # Print representation of database
    print("\n\nDatabase contents:")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT species.common_name, observations.observed_on, observations.latitude, observations.longitude
        FROM observations 
        JOIN species ON observations.taxon_id = species.id
        """
    )
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # Display top 10 most common species
    print("\n\nRanked Species:")
    cursor = conn.cursor()
    ranked_species = rank_species(cursor)
    for species in ranked_species:
        print(f"{species['common_name']} ({species['scientific_name']}): {species['sightings']} sightings")
        image_link = species.get("image_url", "No image available")
        print(f"   Image: {image_link}")
    
    # Display relative abundance of the top 10 species
    print("\n\nRelative Abundance:")
    relative_abundance = rank_relative_abundance(cursor)
    for species in relative_abundance:
        print(f"{species['common_name']} ({species['scientific_name']}): {species['percentage']}%")

    # Display monthly activity trends
    print("\n\nMonthly Activity Trends:")
    monthly_trends = get_monthly_activity_trends(cursor)
    for trend in monthly_trends:
        print(f"{trend['month_name']}: {trend['sightings']} sightings (Species Richness: {trend['species_richness']})")

    # Display biodiversity hotspots
    print("\n\nBiodiversity Hotspots:")
    hotspots = find_biodiversity_hotspots(cursor)
    for spot in hotspots:
        print(f"Grid [{spot['grid_latitude']}, {spot['grid_longitude']}]: {spot['sightings']} sightings, Richness: {spot['species_richness']}")

    # Display seasonal peak for the top ranked species
    print("\n\nSpecies Seasonality Peak:")
    for species in ranked_species:
        peak = get_peak_month_for_species(cursor, species["taxon_id"])
        if peak:
            print(f"{species['common_name']} peak month: {peak['month_name']} with {peak['sightings_in_peak_month']} sightings")

    conn.close()

if __name__ == "__main__":
    run_report_pipeline()