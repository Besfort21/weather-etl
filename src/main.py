import argparse
import logging
import sys
from pathlib import Path

from src.pipeline import WeatherPipeline
from src.scheduler.pipeline_scheduler import PipelineScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Weather ETL Pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run", help="Run the pipeline once and exit.")

    subparsers.add_parser("schedule", help="Run the pipeline on a schedule.")

    export_parser = subparsers.add_parser("export", help="Export data to CSV.")
    export_parser.add_argument("--city", help="Filter by city name.")
    export_parser.add_argument("--date", help="Filter by date e.g. 2026-05-10.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = WeatherPipeline(config_path=Path("config.yaml"))

    if args.command == "run":
        summary = pipeline.run()
        logger.info("Done: %s", summary)

    elif args.command == "schedule":
        scheduler = PipelineScheduler(pipeline)
        scheduler.start()

    elif args.command == "export":
        try:
            path = pipeline.export_csv(
                city=args.city,
                date=args.date,
            )
            logger.info("Exported to: %s", path)
        except ValueError as e:
            logger.error("%s", e)
            sys.exit(1)


if __name__ == "__main__":
    main()