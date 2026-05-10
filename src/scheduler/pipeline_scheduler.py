import logging

from apscheduler.schedulers.blocking import BlockingScheduler

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Runs the ETL pipeline on a fixed interval using APScheduler."""

    def __init__(self, pipeline, interval_hours: int = 1) -> None:
        self._pipeline = pipeline
        self._interval_hours = interval_hours
        self._scheduler = BlockingScheduler()

    def start(self) -> None:
        """Starts the scheduler — blocks until interrupted."""
        self._scheduler.add_job(
            self._pipeline.run,
            trigger="interval",
            hours=self._interval_hours,
            id="weather_etl",
        )
        logger.info(
            "Scheduler started — running every %d hour(s). Press Ctrl+C to stop.",
            self._interval_hours,
        )
        try:
            self._pipeline.run()
            self._scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")