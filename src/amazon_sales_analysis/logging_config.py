from __future__ import annotations

import logging

from amazon_sales_analysis.config import get_settings

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | env=%(environment)s | run_id=%(run_id)s | "
    "%(name)s | %(message)s"
)


class PipelineContextFilter(logging.Filter):
    def __init__(self, environment: str, run_id: str = "n/a") -> None:
        super().__init__()
        self.environment = environment
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "environment"):
            record.environment = self.environment
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        return True


def configure_logging(level: int | None = None, *, run_id: str = "n/a") -> None:
    settings = get_settings()
    resolved_level = (
        level if level is not None else getattr(logging, settings.log_level, logging.INFO)
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(PipelineContextFilter(environment=settings.environment, run_id=run_id))

    root_logger.setLevel(resolved_level)
    root_logger.addHandler(handler)
