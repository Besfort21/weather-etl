import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class CsvExporter:
    """Exports weather DataFrames to CSV files."""

    def __init__(self, export_dir: Path) -> None:
        self._export_dir = export_dir
        self._export_dir.mkdir(parents=True, exist_ok=True)

    def export(self, df: pd.DataFrame, filename: str | None = None) -> Path:
        """Exports a DataFrame to CSV. Auto-generates filename if not provided.

        Returns the path of the written file.
        """
        if df.empty:
            logger.warning("Empty DataFrame — nothing to export.")
            raise ValueError("Cannot export an empty DataFrame.")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weather_export_{timestamp}.csv"

        output_path = self._export_dir / filename
        df.to_csv(output_path, index=False)
        logger.info("Exported %d rows to %s", len(df), output_path)
        return output_path