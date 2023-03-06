import logging
import logging.handlers
from logging import FileHandler, Logger
from pathlib import Path

from napi.settings import ENV


def create_logger(service: str, log_file: str, level: int = logging.INFO) -> Logger:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(service)
    logger.setLevel(logging.DEBUG)

    fh = FileHandler(log_file, "a")
    fh.setLevel(level)
    formatter = logging.Formatter(
        f"{{asctime}}.{{msecs:03.0f}} - {{name}} - {ENV} - {{levelname}} - {{message}}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


core_logger = create_logger("napi", "napi.log", level=logging.DEBUG)
