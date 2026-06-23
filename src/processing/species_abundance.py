
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

