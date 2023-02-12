import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt


DB_FILE = "meterreading.db"
EXAMPLE_FILE = "mr-examples.json"

COUNT_UP_DEVICES_CONFIGURATION = [
    {
        "name": "Gas",
        "column": "gas",
        "unit": "m³",
        "lightColor": "DarkSalmon",
        "darkColor": "red",
    },
    {
        "name": "Water",
        "column": "water",
        "unit": "m³",
        "lightColor": "CornFlowerBlue",
        "darkColor": "Blue",
    },
    {
        "name": "Electricity",
        "column": "electricity",
        "unit": "kWh",
        "lightColor": "LimeGreen",
        "darkColor": "Green",
    },
]

ENSURE_MR_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS mr (
        id integer PRIMARY KEY,
        rdate datetime NOT NULL,
        gas float NOT NULL,
        water float NOT NULL,
        electricity float NOT NULL
    );
"""

DROP_MR_TABLE = """
    DROP TABLE IF EXISTS mr;
"""

MR_INSERT_SQL = """
    INSERT INTO mr (rdate, gas, water, electricity)
        VALUES(?, ?, ?, ?);
"""

MR_SELECT_SQL = """
    SELECT id, rdate, gas, water, electricity FROM mr ORDER BY rdate ASC;
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
    values = (entry["rdate"], entry["gas"], entry["water"], entry["electricity"])
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

    columns = "id rdate gas water electricity".split()
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


class CountUpDevice:

    def __init__(self, name: str, column: str, unit: str, lightColor: str, darkColor: str):
        self.name = name
        self.column = column
        self.unit = unit
        self.lightColor = lightColor
        self.darkColor = darkColor

        self.per_day = None
        self.per_year = None
        self.years = []


    def set_values(self, values: pd.DataFrame):
        df = values.dropna().copy()
        df["d_value"] = (df[self.column] - df[self.column].shift())
        df["per_day"] = df["d_value"] / df.days
        df = df.query("per_day > 0")

        latest_entry = values.iloc[-1]
        day_of_year = latest_entry["day_of_year"]

        self.per_day = df.copy()
        self.per_year = df.groupby("year")["d_value"].sum()
        self.until_day_of_year = df[df["day_of_year"] <= day_of_year].groupby("year")["d_value"].sum()


    def has_per_day_values(self) -> bool:
        return self.per_day.shape[0] > 0


    def has_per_year_values(self) -> bool:
        return self.per_year.shape[0] > 0


    def get_per_day_fig(self):
        fig, ax = plt.subplots()
        plt.plot_date(self.per_day["datetime"], self.per_day["per_day"], fmt="-", color=self.darkColor);
        plt.title(f"Mean {self.name} per day in {self.unit}")
        return fig


    def get_per_day_of_year_fig(self, selected_year: str):
        years = sorted(set(self.per_day.year.to_list()))
        fig, ax = plt.subplots()
        ax.set_xticks(list(range(13)))
        for year in years:
            y = self.per_day.query(f"year == {year}")
            plt.plot(y["m_of_year"], y["per_day"], c="LightGrey", label="")
        y = self.per_day.query(f"year == {selected_year}")
        plt.plot(y["m_of_year"], y["per_day"], c=self.darkColor, label=selected_year)
        plt.legend()
        plt.grid()
        plt.title(f"Mean {self.name} per Day of Year in {self.unit}")
        return fig


    def get_per_year_fig(self):
        fig, ax = plt.subplots()
        plt.bar(x=self.per_year.index, height=self.per_year.values, color=self.lightColor)
        plt.bar(x=self.until_day_of_year.index, height=self.until_day_of_year.values, color=self.darkColor)
        plt.title(f"Total {self.name} in {self.unit}")
        return fig
