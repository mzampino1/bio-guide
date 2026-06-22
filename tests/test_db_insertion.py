from unittest.mock import patch
from src.database.db_insertion import reset_db, init_db, insert_data

# Mock data simulating a typical iNaturalist response snippet
MOCK_OBSERVATIONS = [
    {
        "id": 101,
        "latitude": 40.78,
        "longitude": -73.96,
        "observed_on": "2026-06-01",
        "taxon": {
            "id": 5001,
            "name": "Acer rubrum",
            "preferred_common_name": "Red Maple",
            "default_photo": {"medium_url": "http://example.com/maple.jpg"}
        }
    }
]

@patch('src.database.db_insertion.sqlite3.connect')
def test_reset_db_drops_tables(mock_connect):
    """
    Verifies that reset_db executes DROP TABLE statements for both tables.
    """
    mock_conn = mock_connect.return_value
    mock_cursor = mock_conn.cursor.return_value

    reset_db()

    # Check that connection targets the correct file
    mock_connect.assert_called_with(r"tmp\bioguide.db")
    
    # Verify it attempted to drop both tables
    assert mock_cursor.execute.call_count == 2
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('src.database.db_insertion.sqlite3.connect')
def test_init_db_creates_tables(mock_connect):
    """
    Verifies that init_db executes CREATE TABLE statements for both tables.
    """
    mock_conn = mock_connect.return_value
    mock_cursor = mock_conn.cursor.return_value

    init_db()

    assert mock_cursor.execute.call_count == 2
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('src.database.db_insertion.sqlite3.connect')
def test_insert_data_success(mock_connect):
    """
    Verifies that insert_data attempts to write to both species and observations.
    """
    mock_conn = mock_connect.return_value
    mock_cursor = mock_conn.cursor.return_value

    insert_data(MOCK_OBSERVATIONS)

    assert mock_cursor.execute.call_count == 2
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('src.database.db_insertion.sqlite3.connect')
def test_insert_data_missing_taxon(mock_connect):
    """
    Verifies that observations without a taxon skip the species table write.
    """
    mock_conn = mock_connect.return_value
    mock_cursor = mock_conn.cursor.return_value

    bad_obs = [{"id": 102, "latitude": 0, "longitude": 0, "observed_on": "2026-01-01"}]
    
    insert_data(bad_obs)

    # Should skip the species table and only execute the observation write
    assert mock_cursor.execute.call_count == 1
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()