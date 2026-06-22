import sqlite3

DB_NAME = r"tmp\bioguide.db"

def reset_db():
    """
    Resets the database by dropping the existing tables.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Removes the tables entirely
    cursor.execute("DROP TABLE IF EXISTS observations")
    cursor.execute("DROP TABLE IF EXISTS species")
    conn.commit()
    conn.close()

def init_db():
    """
    Initializes the SQLite database and creates the necessary tables.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Species table
    cursor.execute('''
        CREATE TABLE species (
            id INTEGER PRIMARY KEY,
            scientific_name TEXT,
            common_name TEXT,
            image_url TEXT
        )
    ''')
    
    # 2. Observations table (Links to species via taxon_id)
    cursor.execute('''
        CREATE TABLE observations (
            id INTEGER PRIMARY KEY,
            taxon_id INTEGER,
            latitude REAL,
            longitude REAL,
            observed_on TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(observations):
    """
    Inserts observation data into the SQLite database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for obs in observations:
        taxon = obs.get("taxon") or {}
        taxon_id = taxon.get("id")

        # 1. Insert into species table
        if taxon_id:
            cursor.execute('''
                INSERT OR IGNORE INTO species (id, scientific_name, common_name, image_url)
                VALUES (?, ?, ?, ?)
            ''', (
                taxon_id,
                taxon.get("name"),
                taxon.get("preferred_common_name"),
                # Extract image URL safely
                taxon.get("default_photo", {}).get("medium_url") if taxon.get("default_photo") else None
                )
            )

        # 2. Insert into 'observations' table
        cursor.execute('''
            INSERT OR IGNORE INTO observations 
            (id, taxon_id, latitude, longitude, observed_on)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            obs.get("id"),
            taxon_id,
            obs.get("latitude"),
            obs.get("longitude"),
            obs.get("observed_on")
        ))

    conn.commit()
    conn.close()
    print("Data insertion complete.")
