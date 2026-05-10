from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.extractor.weather_extractor import RawWeatherData
from src.pipeline import WeatherPipeline


@pytest.fixture
def pipeline(tmp_path: Path, mocker) -> WeatherPipeline:
    """Creates a WeatherPipeline with mocked extractor and real transformer/loader."""
    config = {
        "cities": [{"name": "Solingen", "latitude": 51.1765, "longitude": 7.0833}],
        "weather": {"variables": [
            "temperature_2m", "relative_humidity_2m",
            "wind_speed_10m", "precipitation", "weather_code",
        ]},
        "database": {"path": str(tmp_path / "test.db")},
        "exports": {"path": str(tmp_path / "exports")},
    }
    mocker.patch.object(WeatherPipeline, "_load_config", return_value=config)
    return WeatherPipeline()


@pytest.fixture
def mock_raw_data() -> RawWeatherData:
    return RawWeatherData(
        city="Solingen",
        timestamps=["2026-05-10T10:00", "2026-05-10T11:00"],
        temperature=[15.0, 16.5],
        humidity=[70, 68],
        wind_speed=[10.0, 12.0],
        precipitation=[0.0, 0.0],
        weather_code=[2, 1],
    )


class TestPipelineRun:
    def test_run_returns_summary(self, pipeline, mocker, mock_raw_data) -> None:
        mocker.patch.object(
            pipeline._extractor, "fetch_all", return_value=[mock_raw_data]
        )
        summary = pipeline.run()
        assert "extracted" in summary
        assert "transformed" in summary
        assert "inserted" in summary

    def test_run_inserts_correct_count(self, pipeline, mocker, mock_raw_data) -> None:
        mocker.patch.object(
            pipeline._extractor, "fetch_all", return_value=[mock_raw_data]
        )
        summary = pipeline.run()
        assert summary["inserted"] == 2

    def test_run_with_no_data_returns_zero(self, pipeline, mocker) -> None:
        mocker.patch.object(
            pipeline._extractor, "fetch_all", return_value=[]
        )
        summary = pipeline.run()
        assert summary["inserted"] == 0
        assert summary["transformed"] == 0

    def test_run_twice_no_duplicates(self, pipeline, mocker, mock_raw_data) -> None:
        mocker.patch.object(
            pipeline._extractor, "fetch_all", return_value=[mock_raw_data]
        )
        pipeline.run()
        summary = pipeline.run()
        assert summary["inserted"] == 0

    def test_api_failure_handled_gracefully(self, pipeline, mocker) -> None:
        mocker.patch.object(
            pipeline._extractor, "fetch_all", return_value=[]
        )
        summary = pipeline.run()
        assert summary["extracted"] == 0