import logging
from pathlib import Path

import yaml

from src.extractor.weather_extractor import CityConfig, WeatherExtractor
from src.loader.csv_exporter import CsvExporter
from src.loader.db_loader import DbLoader
from src.transformer.weather_transformer import WeatherTransformer

logger = logging.getLogger(__name__)


class WeatherPipeline:
    """Orchestrates the full ETL pipeline: extract → transform → load."""

    def __init__(self, config_path: Path = Path("config.yaml")) -> None:
        config = self._load_config(config_path)

        self._cities = [
            CityConfig(
                name=c["name"],
                latitude=c["latitude"],
                longitude=c["longitude"],
            )
            for c in config["cities"]
        ]

        self._extractor = WeatherExtractor(config["weather"]["variables"])
        self._transformer = WeatherTransformer()
        self._loader = DbLoader(Path(config["database"]["path"]))
        self._exporter = CsvExporter(Path(config["exports"]["path"]))

    def run(self) -> dict:
        """Runs one full ETL cycle. Returns a summary dict."""
        logger.info("Pipeline started for %d cities.", len(self._cities))

        raw_data = self._extractor.fetch_all(self._cities)
        logger.info("Extracted data for %d / %d cities.", len(raw_data), len(self._cities))

        df = self._transformer.transform_all(raw_data)
        if df.empty:
            logger.warning("No data after transformation — aborting load.")
            return {"extracted": len(raw_data), "transformed": 0, "inserted": 0}

        inserted = self._loader.load(df)

        summary = {
            "extracted": len(raw_data),
            "transformed": len(df),
            "inserted": inserted,
        }
        logger.info("Pipeline finished: %s", summary)
        return summary

    def export_csv(self, city: str | None = None, date: str | None = None) -> Path:
        """Queries the database and exports results to CSV."""
        df = self._loader.query(city=city, date=date)
        if df.empty:
            raise ValueError("No data found for the given filters.")
        return self._exporter.export(df)

    @staticmethod
    def _load_config(config_path: Path) -> dict:
        """Loads and returns the YAML config file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path) as f:
            return yaml.safe_load(f)