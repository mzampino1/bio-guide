from datetime import datetime, timedelta
import requests
import time

BASE_URL = "https://api.inaturalist.org/v1/observations"

def get_location_observations(lat, lng, radius=5, bbox=None, max_observations=5000):
    """
    Fetches a small batch of recent observations from iNaturalist based on coordinates.
    """
    
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "per_page": 200,
        "order": "desc",
        "order_by": "created_at",
        "d1": one_month_ago
    }

    if bbox:
        params.update({
            "swlat": bbox["swlat"],
            "swlng": bbox["swlng"],
            "nelat": bbox["nelat"],
            "nelng": bbox["nelng"],
        })
    else:
        params.update({
            "lat": lat,
            "lng": lng,
            "radius": radius
        })

    headers = {
        "User-Agent": "BioGuide/1.0 (https://github.com/mzampino1/bio-guide)"
    }
    
    all_observations = []
    current_page = 1

    while len(all_observations) < max_observations:
        params["page"] = current_page
        
        try:
            print(f"Fetching page {current_page} (Collected so far: {len(all_observations)})...")
            response = requests.get(BASE_URL, params=params, headers=headers)
            response.raise_for_status() 
            data = response.json()
            
            results = data.get("results", [])
            if not results:
                print("No more observations matching these parameters found. Ending search.")
                break
                
            all_observations.extend(results)
            
            # If the server hands back a batch smaller than our requested limit,
            # we've reached the absolute end of their record index for this area.
            if len(results) < params["per_page"]:
                print("Final incomplete page received. Ending search.")
                break
                
            current_page += 1
            
            # Rate limiting to avoid overwhelming the API
            time.sleep(1.5)
            
        except requests.exceptions.RequestException as e:
            print(f"API Request failed on page {current_page}: {e}")
            break

    # Truncate results cleanly if a final page pushed slightly past the limit
    return all_observations[:max_observations]
