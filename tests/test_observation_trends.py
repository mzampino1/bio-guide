import sqlite3
from src.processing.observation_trends import (
    get_monthly_activity_trends, 
    find_biodiversity_hotspots, 
    get_peak_month_for_species
)

MOCK_SPECIES_ROWS = [
    (5001, "Acer rubrum", "Red Maple", "http://example.com/maple.jpg"),
    (5002, "Cyanocitta cristata", "Blue Jay", "http://example.com/bluejay.jpg")
]

# Test data: 
# 4 sightings happen in June (06), 1 in July (07)
# 4 sightings cluster closely in Area A containing 2 distinct species
# 1 sighting sits isolated in Area B containing only 1 species
MOCK_OBSERVATION_ROWS = [
    # Area A Grid (June) - Adjusted to match perfectly at 3 decimal places
    (1, 5001, 40.712, -73.916, "2026-06-01"),
    (2, 5001, 40.712, -73.916, "2026-06-02"),
    (3, 5002, 40.712, -73.916, "2026-06-03"),
    (4, 5002, 40.712, -73.916, "2026-06-15"),
    
    # Area B Grid (July) - Adjusted to 3 decimal places
    (5, 5001, 34.051, -118.243, "2026-07-04")
]

def create_test_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE species (
            id INTEGER PRIMARY KEY, scientific_name TEXT, common_name TEXT, image_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY, taxon_id INTEGER, latitude REAL, longitude REAL, observed_on TEXT
        )
    ''')
    cursor.executemany("INSERT INTO species VALUES (?, ?, ?, ?)", MOCK_SPECIES_ROWS)
    cursor.executemany("INSERT INTO observations VALUES (?, ?, ?, ?, ?)", MOCK_OBSERVATION_ROWS)
    conn.commit()
    return conn, cursor


def test_get_monthly_activity_trends():
    """Verify that observations are aggregated and sorted accurately by month groups."""
    conn, cursor = create_test_db()

    trends = get_monthly_activity_trends(cursor)

    assert isinstance(trends, list)
    assert len(trends) == 2  # June and July

    # First entry should be June (06)
    assert trends[0]["month_num"] == "06"
    assert trends[0]["month_name"] == "June"
    assert trends[0]["sightings"] == 4
    assert trends[0]["species_richness"] == 2  # Both Maple and Blue Jay seen in June

    # Second entry should be July (07)
    assert trends[1]["month_num"] == "07"
    assert trends[1]["month_name"] == "July"
    assert trends[1]["sightings"] == 1
    assert trends[1]["species_richness"] == 1  # Only Maple seen in July

    conn.close()


def test_find_biodiversity_hotspots():
    """Verify that coordinates group into grids and rank correctly by species richness."""
    conn, cursor = create_test_db()

    hotspots = find_biodiversity_hotspots(cursor, limit=5)

    assert isinstance(hotspots, list)
    assert len(hotspots) == 2  # Two distinct rounded coordinate regions

    # The Area A cluster should rank #1 because it has 2 unique species
    assert hotspots[0]["grid_latitude"] == 40.712
    assert hotspots[0]["grid_longitude"] == -73.916
    assert hotspots[0]["species_richness"] == 2
    assert hotspots[0]["sightings"] == 4

    # The Area B sighting should rank #2
    assert hotspots[1]["grid_latitude"] == 34.051
    assert hotspots[1]["grid_longitude"] == -118.243
    assert hotspots[1]["species_richness"] == 1
    assert hotspots[1]["sightings"] == 1

    conn.close()

def test_get_peak_month_for_species_success():
    """
    Verify that the peak observation month is correctly identified for a 
    given species based on the highest count.
    """
    conn, cursor = create_test_db()

    # Red Maple (5001) has 2 sightings in June and 1 in July. June should win.
    result = get_peak_month_for_species(cursor, taxon_id=5001)

    assert result is not None
    assert result["taxon_id"] == 5001
    assert result["month_num"] == "06"
    assert result["month_name"] == "June"
    assert result["sightings_in_peak_month"] == 2

    conn.close()


def test_get_peak_month_for_missing_species():
    """
    Ensure the function returns None gracefully if requested to analyze a 
    species ID that does not exist in the observation logs.
    """
    conn, cursor = create_test_db()

    # Query an ID that has zero entries in our transient database environment
    result = get_peak_month_for_species(cursor, taxon_id=9999)

    assert result is None

    conn.close()