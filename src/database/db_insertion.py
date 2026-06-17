import sqlite3

DB_NAME = "bioguide.db"

def init_db():
    """
    Initializes the SQLite database and creates the necessary tables.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Species table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS species (
            id INTEGER PRIMARY KEY,
            scientific_name TEXT,
            common_name TEXT,
            image_url TEXT
        )
    ''')
    
    # 2. Observations table (Links to species via taxon_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY,
            taxon_id INTEGER,
            latitude REAL,
            longitude REAL,
            observed_on TEXT
        )
    ''')
    conn.commit()
    conn.close()

