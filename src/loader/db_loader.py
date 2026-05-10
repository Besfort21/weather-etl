import logging
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DbLoader:
    """Loads transformed weather data into SQLite, skipping duplicates."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Creates the weather table if it doesn't exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    city              TEXT    NOT NULL,
                    timestamp         TEXT    NOT NULL,
                    temperature_c     REAL    NOT NULL,
                    feels_like_c      REAL    NOT NULL,
                    humidity_pct      INTEGER NOT NULL,
                    wind_speed_kmh    REAL    NOT NULL,
                    precipitation_mm  REAL    NOT NULL,
                    weather_code      INTEGER NOT NULL,
                    weather_description TEXT  NOT NULL,
                    UNIQUE(city, timestamp)
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def load(self, df: pd.DataFrame) -> int:
        """Inserts rows into the database, skipping duplicates.

        Returns the number of newly inserted rows.
        """
        if df.empty:
            logger.warning("Empty DataFrame — nothing to load.")
            return 0

        rows_before = self._count_rows()

        with self._connect() as conn:
            for _, row in df.iterrows():
                conn.execute(
                    """
                    INSERT OR IGNORE INTO weather
                        (city, timestamp, temperature_c, feels_like_c,
                         humidity_pct, wind_speed_kmh, precipitation_mm,
                         weather_code, weather_description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["city"],
                        row["timestamp"].isoformat(),
                        row["temperature_c"],
                        row["feels_like_c"],
                        int(row["humidity_pct"]),
                        row["wind_speed_kmh"],
                        row["precipitation_mm"],
                        int(row["weather_code"]),
                        row["weather_description"],
                    ),
                )

        rows_inserted = self._count_rows() - rows_before
        logger.info("Inserted %d new rows (skipped duplicates).", rows_inserted)
        return rows_inserted

    def _count_rows(self) -> int:
        """Returns the total number of rows in the weather table."""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM weather").fetchone()[0]

    def query(self, city: str | None = None, date: str | None = None) -> pd.DataFrame:
        """Queries weather data with optional filters.

        Args:
            city: filter by city name (exact match)
            date: filter by date string e.g. '2026-05-10'
        """
        query = "SELECT * FROM weather WHERE 1=1"
        params: list = []

        if city:
            query += " AND city = ?"
            params.append(city)
        if date:
            query += " AND timestamp LIKE ?"
            params.append(f"{date}%")

        query += " ORDER BY city, timestamp"

        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)