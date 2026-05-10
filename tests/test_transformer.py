import pandas as pd
import pytest

from src.extractor.weather_extractor import RawWeatherData
from src.transformer.weather_transformer import WeatherTransformer


@pytest.fixture
def transformer() -> WeatherTransformer:
    return WeatherTransformer()


@pytest.fixture
def raw_data() -> RawWeatherData:
    return RawWeatherData(
        city="Solingen",
        timestamps=["2026-05-10T10:00", "2026-05-10T11:00", "2026-05-10T12:00"],
        temperature=[15.0, 16.5, 17.2],
        humidity=[70, 68, 65],
        wind_speed=[10.0, 12.0, 8.0],
        precipitation=[0.0, 0.0, 0.1],
        weather_code=[2, 1, 0],
    )


class TestTransform:
    def test_returns_dataframe(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert isinstance(df, pd.DataFrame)

    def test_correct_row_count(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert len(df) == 3

    def test_city_column_correct(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert all(df["city"] == "Solingen")

    def test_timestamp_is_datetime(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_weather_description_added(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert "weather_description" in df.columns

    def test_weather_description_correct(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert df.iloc[2]["weather_description"] == "Clear sky"

    def test_feels_like_column_added(self, transformer, raw_data) -> None:
        df = transformer.transform(raw_data)
        assert "feels_like_c" in df.columns

    def test_drops_rows_with_missing_values(self, transformer) -> None:
        raw = RawWeatherData(
            city="Solingen",
            timestamps=["2026-05-10T10:00", "2026-05-10T11:00"],
            temperature=[None, 16.5],
            humidity=[70, 68],
            wind_speed=[10.0, 12.0],
            precipitation=[0.0, 0.0],
            weather_code=[2, 1],
        )
        df = transformer.transform(raw)
        assert len(df) == 1

    def test_returns_none_on_invalid_data(self, transformer) -> None:
        raw = RawWeatherData(
            city="Solingen",
            timestamps=["not-a-date"],
            temperature=["not-a-float"],
            humidity=[70],
            wind_speed=[10.0],
            precipitation=[0.0],
            weather_code=[2],
        )
        df = transformer.transform(raw)
        assert df is None


class TestTransformAll:
    def test_concatenates_multiple_cities(self, transformer, raw_data) -> None:
        raw2 = RawWeatherData(
            city="Köln",
            timestamps=["2026-05-10T10:00", "2026-05-10T11:00", "2026-05-10T12:00"],
            temperature=[14.0, 15.0, 16.0],
            humidity=[72, 70, 68],
            wind_speed=[9.0, 11.0, 7.0],
            precipitation=[0.0, 0.0, 0.0],
            weather_code=[1, 1, 0],
        )
        df = transformer.transform_all([raw_data, raw2])
        assert len(df) == 6

    def test_returns_empty_dataframe_on_empty_input(self, transformer) -> None:
        df = transformer.transform_all([])
        assert df.empty


class TestFeelsLike:
    def test_returns_temperature_when_wind_low(self) -> None:
        result = WeatherTransformer._feels_like(15.0, 3.0)
        assert result == 15.0

    def test_feels_colder_with_high_wind(self) -> None:
        result = WeatherTransformer._feels_like(15.0, 30.0)
        assert result < 15.0