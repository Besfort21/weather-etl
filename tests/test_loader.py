from pathlib import Path

import pandas as pd
import pytest

from src.loader.csv_exporter import CsvExporter
from src.loader.db_loader import DbLoader


@pytest.fixture
def loader(tmp_path: Path) -> DbLoader:
    """Creates a DbLoader with a temp SQLite database."""
    return DbLoader(tmp_path / "test.db")


@pytest.fixture
def exporter(tmp_path: Path) -> CsvExporter:
    """Creates a CsvExporter with a temp export directory."""
    return CsvExporter(tmp_path / "exports")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Solingen", "Solingen"],
        "timestamp": pd.to_datetime(["2026-05-10T10:00", "2026-05-10T11:00"]),
        "temperature_c": [15.0, 16.5],
        "feels_like_c": [13.0, 14.2],
        "humidity_pct": [70, 68],
        "wind_speed_kmh": [10.0, 12.0],
        "precipitation_mm": [0.0, 0.0],
        "weather_code": [2, 1],
        "weather_description": ["Partly cloudy", "Mainly clear"],
    })


class TestDbLoader:
    def test_load_returns_correct_count(self, loader, sample_df) -> None:
        inserted = loader.load(sample_df)
        assert inserted == 2

    def test_load_empty_dataframe_returns_zero(self, loader) -> None:
        inserted = loader.load(pd.DataFrame())
        assert inserted == 0

    def test_duplicate_rows_not_inserted(self, loader, sample_df) -> None:
        loader.load(sample_df)
        inserted_again = loader.load(sample_df)
        assert inserted_again == 0

    def test_query_returns_all_rows(self, loader, sample_df) -> None:
        loader.load(sample_df)
        result = loader.query()
        assert len(result) == 2

    def test_query_filter_by_city(self, loader, sample_df) -> None:
        loader.load(sample_df)
        result = loader.query(city="Solingen")
        assert len(result) == 2

    def test_query_nonexistent_city_returns_empty(self, loader, sample_df) -> None:
        loader.load(sample_df)
        result = loader.query(city="Berlin")
        assert result.empty

    def test_query_filter_by_date(self, loader, sample_df) -> None:
        loader.load(sample_df)
        result = loader.query(date="2026-05-10")
        assert len(result) == 2

    def test_query_wrong_date_returns_empty(self, loader, sample_df) -> None:
        loader.load(sample_df)
        result = loader.query(date="2025-01-01")
        assert result.empty


class TestCsvExporter:
    def test_export_creates_file(self, exporter, sample_df) -> None:
        path = exporter.export(sample_df)
        assert path.exists()

    def test_export_correct_row_count(self, exporter, sample_df) -> None:
        path = exporter.export(sample_df)
        df = pd.read_csv(path)
        assert len(df) == 2

    def test_export_raises_on_empty_dataframe(self, exporter) -> None:
        with pytest.raises(ValueError):
            exporter.export(pd.DataFrame())

    def test_export_custom_filename(self, exporter, sample_df) -> None:
        path = exporter.export(sample_df, filename="test_export.csv")
        assert path.name == "test_export.csv"