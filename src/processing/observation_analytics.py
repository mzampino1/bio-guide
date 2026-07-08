def get_monthly_activity_trends(cursor):
    """
    Extracts the month from the 'observed_on' text column to analyze seasonal activity.
    Returns a sorted list of months showing when wildlife sightings spike.
    """
    query = """
        SELECT 
            strftime('%m', observed_on) as month_num,
            COUNT(id) as total_sightings,
            COUNT(DISTINCT taxon_id) as unique_species_seen
        FROM observations
        GROUP BY month_num
        ORDER BY month_num ASC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Optional dictionary mapping to convert SQLite strings ("06") into clear labels
    month_names = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }
    
    return [
        {
            "month_num": r[0],
            "month_name": month_names.get(r[0], "Unknown"),
            "sightings": r[1],
            "species_richness": r[2]
        }
        for r in rows
    ]

def get_peak_month_for_species(cursor, taxon_id):
    """
    Identifies the calendar month when a specific species is most 
    frequently observed based on historical database records.
    """
    query = """
        SELECT 
            strftime('%m', observed_on) as month_num,
            COUNT(id) as sighting_count
        FROM observations
        WHERE taxon_id = ?
        GROUP BY month_num
        ORDER BY sighting_count DESC
        LIMIT 1;
    """
    cursor.execute(query, (taxon_id,))
    row = cursor.fetchone()
    
    if not row:
        return None  # Handle edge-case where species has zero logged observations
        
    month_names = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }
    
    return {
        "taxon_id": taxon_id,
        "month_num": row[0],
        "month_name": month_names.get(row[0], "Unknown"),
        "sightings_in_peak_month": row[1]
    }