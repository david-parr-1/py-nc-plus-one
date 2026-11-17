import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def configure_logging() -> None:
    load_dotenv()
    root_logger = logging.getLogger()
    root_logger.setLevel(os.getenv("LOGGING_LEVEL", "INFO"))

    if root_logger.handlers:
        return

    formatter = JSONFormatter()

    file_name = "nc-plus-one-log.jsonl"
    file_path = Path("./logs/")
    os.makedirs(file_path, exist_ok=True)

    file_handler = logging.FileHandler(
        os.path.join(file_path, file_name), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
