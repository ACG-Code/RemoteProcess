"""
RemoteProcess.py

Usage:
    RemoteProcess.py -h | --help
    RemoteProcess.py --version
    RemoteProcess.py <tm1> <process> <parameters>

Options:
    -h --help       Show this screen.
    --version       Show version.

Positional Arguments:
    tm1              TM1 server name (must match a section in config.ini)
    process          TM1 process name to execute
    parameters       Semicolon-separated key=value pairs e.g. "pParam1=value1;pParam2=42"
"""

import logging
import os
import re
import sys

from docopt import docopt
from TM1py import TM1Service

import logging_config
from ConfigManager import get_tm1_connection

log = logging.getLogger(__name__)

_FALLBACK_VERSION = "1.0.0"


def _get_version() -> str:
    # Resolve version file whether running frozen (PyInstaller) or as a script
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.join(os.path.dirname(__file__), "..")

    version_file = os.path.join(base, "app_version.txt")
    if not os.path.isfile(version_file):
        return _FALLBACK_VERSION

    with open(version_file, "r") as f:
        content = f.read()

    match = re.search(r"FileVersion',\s*'([\d.]+)'", content)
    return match.group(1) if match else _FALLBACK_VERSION


APP_VERSION = _get_version()


def _parse_parameters(raw: str) -> dict:
    """Parse 'key=value;key=value' into a dict, coercing numeric strings to int or float."""
    if not raw.strip():
        return {}
    params = {}
    for pair in raw.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise ValueError(f"Expected 'key=value', got: '{pair}'")
        key, _, value = pair.partition("=")
        key = key.strip()
        value = value.strip()
        # Coerce to int or float when possible so TM1 numeric params are typed correctly
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        params[key] = value
    return params


def main():
    logging_config.configure()

    args = docopt(__doc__, version=APP_VERSION, options_first=True)

    server_name = args["<tm1>"]
    process_name = args["<process>"]
    raw_params = args["<parameters>"]

    log.debug("Arguments received: server=%s process=%s", server_name, process_name)

    try:
        parameters = _parse_parameters(raw_params)
    except ValueError as e:
        log.error("Invalid parameters: %s", e)
        sys.exit(1)

    try:
        conn = get_tm1_connection(server_name)
    except (FileNotFoundError, KeyError) as e:
        log.error("Config error: %s", e)
        sys.exit(1)

    log.info("Connecting to TM1 server '%s'", server_name)
    try:
        with TM1Service(**conn) as tm1:
            log.info("Executing process '%s' with parameters: %s", process_name, parameters)
            success, status, error_log_file = tm1.processes.execute_with_return(
                process_name, **parameters
            )
    except Exception:
        log.exception("Unexpected error while executing process '%s'", process_name)
        sys.exit(1)

    if success:
        log.info("Process '%s' completed successfully (status: %s)", process_name, status)
    else:
        log.error(
            "Process '%s' failed (status: %s, log: %s)", process_name, status, error_log_file
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
