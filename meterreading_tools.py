import sqlite3
import json
import pandas as pd


DB_FILE = "meterreading.db"
EXAMPLE_FILE = "mr-examples.json"

ENSURE_MR_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS mr (
        id integer PRIMARY KEY,
        rdate datetime NOT NULL,
        gas float NOT NULL
    );
"""

DROP_MR_TABLE = """
    DROP TABLE IF EXISTS mr;
"""

MR_INSERT_SQL = """
    INSERT INTO mr (rdate, gas)
        VALUES(?, ?);
"""

MR_SELECT_SQL = """
    SELECT id, rdate, gas FROM mr ORDER BY rdate ASC;
"""


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def ensure_tables(conn):
    cur = conn.cursor()
    cur.execute(ENSURE_MR_TABLE_SQL)
    conn.commit()


def drop_tables():
    conn = create_connection(DB_FILE)
    cur = conn.cursor()
    cur.execute(DROP_MR_TABLE)
    conn.commit()
    conn.close()


def create_entry(conn, entry):
    """Put a new entry into the database
    :param conn: connection object
    :param entry: entry to be stored
    """
    values = (entry["rdate"], entry["gas"])
    cur = conn.cursor()
    cur.execute(MR_INSERT_SQL, values)
    conn.commit()


def select_all_entries(conn):
    """Read all entries from the database table
    :param: connection object
    :return: pd.DataFrame
    """
    cur = conn.cursor()
    cur.execute(MR_SELECT_SQL)
    rows = cur.fetchall()

    columns = "id rdate gas".split()
    df = pd.DataFrame(rows, columns=columns).set_index("id")

    df["datetime"] = pd.to_datetime(df.rdate, unit="ms")
    df["day_of_year"] = df.datetime.dt.dayofyear
    df["m_of_year"] = df["day_of_year"] / 365. * 12.
    df["year"] = df.datetime.dt.year
    df["days"] = (df.rdate - df.rdate.shift())/1000./60./60./24.

    return df


def set_example_data():
    with open(EXAMPLE_FILE) as f:
        entries = json.load(f)
    entries = pd.DataFrame(entries).sort_values("rdate")

    drop_tables()

    conn = create_connection(DB_FILE)
    ensure_tables(conn)

    for _, entry in entries.iterrows():
        create_entry(conn, entry)

    conn.close()
