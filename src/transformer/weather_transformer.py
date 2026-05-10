import logging

import pandas as pd

from src.extractor.weather_extractor import RawWeatherData

logger = logging.getLogger(__name__)

WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Violent showers",
    95: "Thunderstorm",
    99: "Thunderstorm with hail",
}


class WeatherTransformer:
    """Transforms raw weather data into a clean, enriched DataFrame."""

    def transform(self, raw: RawWeatherData) -> pd.DataFrame | None:
        """Transforms a single RawWeatherData object. Returns None on failure."""
        try:
            df = self._build_dataframe(raw)
            df = self._parse_types(df)
            df = self._drop_missing(df)
            df = self._add_derived_columns(df)
            logger.info(
                "Transformed %d rows for %s", len(df), raw.city
            )
            return df
        except Exception as e:
            logger.error("Transform failed for %s: %s", raw.city, e)
            return None

    def transform_all(self, raw_list: list[RawWeatherData]) -> pd.DataFrame:
        """Transforms multiple cities and concatenates into one DataFrame."""
        frames = []
        for raw in raw_list:
            df = self.transform(raw)
            if df is not None:
                frames.append(df)

        if not frames:
            logger.warning("No data to transform.")
            return pd.DataFrame()

        return pd.concat(frames, ignore_index=True)

    def _build_dataframe(self, raw: RawWeatherData) -> pd.DataFrame:
        """Builds the initial DataFrame from raw lists."""
        return pd.DataFrame({
            "city": raw.city,
            "timestamp": raw.timestamps,
            "temperature_c": raw.temperature,
            "humidity_pct": raw.humidity,
            "wind_speed_kmh": raw.wind_speed,
            "precipitation_mm": raw.precipitation,
            "weather_code": raw.weather_code,
        })

    def _parse_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parses and enforces correct column types."""
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["temperature_c"] = df["temperature_c"].astype(float)
        df["humidity_pct"] = df["humidity_pct"].astype(int)
        df["wind_speed_kmh"] = df["wind_speed_kmh"].astype(float)
        df["precipitation_mm"] = df["precipitation_mm"].astype(float)
        df["weather_code"] = df["weather_code"].astype(int)
        return df

    def _drop_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drops rows where any critical column is null."""
        before = len(df)
        df = df.dropna(subset=[
            "timestamp", "temperature_c", "humidity_pct",
            "wind_speed_kmh", "precipitation_mm",
        ])
        dropped = before - len(df)
        if dropped > 0:
            logger.warning("Dropped %d rows with missing values.", dropped)
        return df

    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds enriched columns derived from existing data."""
        df["weather_description"] = df["weather_code"].map(WEATHER_CODES).fillna("Unknown")
        df["feels_like_c"] = df.apply(
            lambda row: self._feels_like(row["temperature_c"], row["wind_speed_kmh"]),
            axis=1,
        ).round(1)
        return df

    @staticmethod
    def _feels_like(temperature: float, wind_speed: float) -> float:
        """Calculates wind chill (feels-like) temperature.

        Uses the Environment Canada wind chill formula.
        Falls back to actual temperature when wind speed is low.
        """
        if wind_speed < 5:
            return temperature
        return (
            13.12
            + 0.6215 * temperature
            - 11.37 * (wind_speed ** 0.16)
            + 0.3965 * temperature * (wind_speed ** 0.16)
        )