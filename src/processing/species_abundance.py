
def rank_species_with_grouping(cursor, limit=10, group=None):
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
    """
    if group == "plants":
        query += " WHERE s.iconic_taxon_name = 'Plantae'"
    elif group == "animals":
        query += " WHERE s.iconic_taxon_name NOT IN ('Plantae', 'Fungi', 'Chromista')"
    
    query += """
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
    Returns the most observed species, each with its percentage
    share of all observations in the database.
    """
    cursor.execute("SELECT COUNT(*) FROM observations;")
    total_observations = cursor.fetchone()[0]
    if total_observations == 0:
        return []

    ranked = rank_species_with_grouping(cursor, limit=limit, group=None)
    for species in ranked:
        species["percentage"] = round((species["sightings"] / total_observations) * 100, 2)
    return ranked