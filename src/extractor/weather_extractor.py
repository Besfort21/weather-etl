import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class CityConfig:
    name: str
    latitude: float
    longitude: float


@dataclass
class RawWeatherData:
    city: str
    timestamps: list[str]
    temperature: list[float]
    humidity: list[int]
    wind_speed: list[float]
    precipitation: list[float]
    weather_code: list[int]


class WeatherExtractor:
    """Fetches raw hourly weather data from the Open-Meteo API."""

    TIMEOUT_SECONDS = 10

    def __init__(self, variables: list[str]) -> None:
        self._variables = variables

    def fetch(self, city: CityConfig) -> RawWeatherData | None:
        """Fetches weather data for one city. Returns None on failure."""
        params = {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "hourly": ",".join(self._variables),
            "forecast_days": 1,
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            return self._parse(city.name, response.json())
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching data for %s", city.name)
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s: %s", city.name, e)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Request failed for %s: %s", city.name, e)
            return None

    def fetch_all(self, cities: list[CityConfig]) -> list[RawWeatherData]:
        """Fetches data for all cities. Skips cities that fail."""
        results = []
        for city in cities:
            logger.info("Fetching data for %s", city.name)
            data = self.fetch(city)
            if data is not None:
                results.append(data)
        return results

    def _parse(self, city_name: str, response: dict) -> RawWeatherData:
        """Parses the API response into a RawWeatherData object."""
        hourly = response["hourly"]
        return RawWeatherData(
            city=city_name,
            timestamps=hourly["time"],
            temperature=hourly["temperature_2m"],
            humidity=hourly["relative_humidity_2m"],
            wind_speed=hourly["wind_speed_10m"],
            precipitation=hourly["precipitation"],
            weather_code=hourly["weather_code"],
        )