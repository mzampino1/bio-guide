
def rank_species(cursor, limit=10):
    """Ranks species by observation count (Finds most common species)."""
    query = """
        SELECT 
            s.id,
            COALESCE(s.common_name, 'Unknown') as common_name, 
            s.scientific_name, 
            s.image_url, 
            COUNT(o.id) as total_sightings
        FROM observations o
        JOIN species s ON o.taxon_id = s.id
        GROUP BY o.taxon_id
        ORDER BY total_sightings DESC
        LIMIT ?;
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    return [
        {"taxon_id": r[0], "common_name": r[1], "scientific_name": r[2], "image_url": r[3], "sightings": r[4]}
        for r in rows
    ]

def rank_relative_abundance(cursor, limit=10):
    """
    Calculates the percentage share of total observations each species holds
    relative to the entire database ecosystem.
    """
    # Avoid a runtime DivisionByZero error if database is empty
    cursor.execute("SELECT COUNT(*) FROM observations;")
    total_observations = cursor.fetchone()[0]
    if total_observations == 0:
        return []

    query = """
        SELECT 
            s.id,
            COALESCE(s.common_name, 'Unknown') as common_name, 
            s.scientific_name, 
            s.image_url, 
            COUNT(o.id) as total_sightings
        FROM observations o
        JOIN species s ON o.taxon_id = s.id
        GROUP BY o.taxon_id
        ORDER BY total_sightings DESC
        LIMIT ?;
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    return [
        {
            "taxon_id": r[0], 
            "common_name": r[1], 
            "scientific_name": r[2], 
            "image_url": r[3], 
            "sightings": r[4],
            # Calculate proportion and round to 2 decimal places
            "percentage": round((r[4] / total_observations) * 100, 2)
        }
        for r in rows
    ]
