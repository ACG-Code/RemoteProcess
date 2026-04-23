import logging
import logging.handlers
import os

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "remoteexecute.log")

_CONSOLE_FORMAT = "%(asctime)s  %(levelname)-8s  %(message)s"
_FILE_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure(level: int = logging.INFO) -> None:
    os.makedirs(os.path.abspath(_LOG_DIR), exist_ok=True)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT))

    # Rotate at 5 MB, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.abspath(_LOG_FILE),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)
