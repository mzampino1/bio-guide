import sqlite3
from src.processing.species_abundance import rank_species_with_grouping, rank_relative_abundance

# Mock species records including the new iconic_taxon_name values
MOCK_SPECIES_ROWS = [
    (5001, "Acer rubrum", "Red Maple", "Plantae", "http://example.com/maple.jpg"),
    (5002, "Cyanocitta cristata", "Blue Jay", "Aves", "http://example.com/bluejay.jpg"),
    (5003, "Taraxacum officinale", None, "Plantae", "http://example.com/dandelion.jpg")  # None triggers COALESCE fallback
]

# Mock observations providing 3 sightings for Maple, 2 for Blue Jay, and 1 for Dandelion
MOCK_OBSERVATION_ROWS = [
    (1, 5001, 40.78, -73.96, "2026-06-01"),
    (2, 5001, 40.79, -73.95, "2026-06-02"),
    (3, 5001, 40.80, -73.94, "2026-06-03"),
    (4, 5002, 40.81, -73.93, "2026-06-04"),
    (5, 5002, 40.82, -73.92, "2026-06-05"),
    (6, 5003, 40.83, -73.91, "2026-06-06")
]

def create_test_db():
    """
    Helper utility to provision a pristine schema in RAM and pre-seed it
    with controlled scenarios before an assertion runs.
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Mirror updated tables from db_insertion.py
    cursor.execute('''
        CREATE TABLE species (
            id INTEGER PRIMARY KEY,
            scientific_name TEXT,
            common_name TEXT,
            iconic_taxon_name TEXT,
            image_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY,
            taxon_id INTEGER,
            latitude REAL,
            longitude REAL,
            observed_on TEXT
        )
    ''')
    
    cursor.executemany("INSERT INTO species VALUES (?, ?, ?, ?, ?)", MOCK_SPECIES_ROWS)
    cursor.executemany("INSERT INTO observations VALUES (?, ?, ?, ?, ?)", MOCK_OBSERVATION_ROWS)
    conn.commit()
    
    return conn, cursor


def test_rank_species_sorting_and_counts():
    """
    Verify that rank_species_with_grouping effectively counts observation volumes and
    sorts them in strict descending order when no group filter is provided.
    """
    conn, cursor = create_test_db()

    results = rank_species_with_grouping(cursor, limit=10)

    assert isinstance(results, list)
    assert len(results) == 3

    # Red Maple (ID 5001) should rank #1 because it has 3 observations
    assert results[0]["taxon_id"] == 5001
    assert results[0]["common_name"] == "Red Maple"
    assert results[0]["sightings"] == 3

    # Blue Jay (ID 5002) should rank #2 because it has 2 observations
    assert results[1]["taxon_id"] == 5002
    assert results[1]["sightings"] == 2

    conn.close()


def test_rank_species_coalesce_fallback():
    """
    Confirm that species entries lacking a preferred common name (NULL)
    are successfully caught by COALESCE and replaced with 'Unknown'.
    """
    conn, cursor = create_test_db()
    results = rank_species_with_grouping(cursor, limit=10)

    # Locate the dandelion row (ID 5003) where common_name was inserted as None
    dandelion = next(row for row in results if row["taxon_id"] == 5003)

    assert dandelion["common_name"] == "Unknown"
    assert dandelion["scientific_name"] == "Taraxacum officinale"

    conn.close()


def test_rank_species_respects_limit_parameter():
    """
    Ensure that the limit argument correctly limits the number of 
    processed dictionary elements returned.
    """
    conn, cursor = create_test_db()

    # Request exclusively the single most common item
    results = rank_species_with_grouping(cursor, limit=1)

    assert len(results) == 1
    assert results[0]["taxon_id"] == 5001  # Should safely match the dominant Maple record

    conn.close()


def test_rank_species_filter_plants():
    """
    Verify that specifying group='plants' filters out non-plant iconic taxa.
    """
    conn, cursor = create_test_db()

    # Request plants only
    results = rank_species_with_grouping(cursor, limit=10, group="plants")

    assert len(results) == 2
    # Should only contain Red Maple and Dandelion
    taxon_ids = [r["taxon_id"] for r in results]
    assert 5001 in taxon_ids
    assert 5003 in taxon_ids
    assert 5002 not in taxon_ids  # Blue Jay excluded

    conn.close()


def test_rank_species_filter_animals():
    """
    Verify that specifying group='animals' excludes plants, fungi, and chromista.
    """
    conn, cursor = create_test_db()

    # Request animals only
    results = rank_species_with_grouping(cursor, limit=10, group="animals")

    assert len(results) == 1
    # Should only contain Blue Jay
    assert results[0]["taxon_id"] == 5002

    conn.close()


def test_rank_relative_abundance_calculations():
    """
    Verify that rank_relative_abundance calculates the proportional percentage 
    of each species relative to total database observations and rounds to 2 decimals.
    """
    conn, cursor = create_test_db()

    results = rank_relative_abundance(cursor, limit=10)

    assert isinstance(results, list)
    assert len(results) == 3

    # Red Maple has 3 out of 6 sightings (50.0%)
    assert results[0]["taxon_id"] == 5001
    assert results[0]["percentage"] == 50.0

    # Blue Jay has 2 out of 6 sightings (33.33%)
    assert results[1]["taxon_id"] == 5002
    assert results[1]["percentage"] == 33.33

    # Dandelion has 1 out of 6 sightings (16.67%)
    assert results[2]["taxon_id"] == 5003
    assert results[2]["percentage"] == 16.67

    conn.close()


def test_rank_relative_abundance_empty_database():
    """
    Ensure that running relative abundance on an empty database handles the
    edge case gracefully and returns an empty list instead of throwing a DivisionByZero error.
    """
    # Create a completely empty in-memory DB structure with no data rows
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE species (id INT);")
    cursor.execute("CREATE TABLE observations (id INT);")
    conn.commit()

    results = rank_relative_abundance(cursor, limit=5)

    assert results == []

    conn.close()