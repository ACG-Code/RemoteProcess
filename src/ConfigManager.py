import configparser
import ctypes
import logging
import os
import sys
from typing import Any

from cryptography.fernet import Fernet

log = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

_DEFAULT_CONFIG_PATH = os.path.join(_BASE_DIR, "config.ini")
_DEFAULT_KEY_PATH = os.path.join(_BASE_DIR, "secret.key")

_BOOL_KEYS = {"ssl", "verify", "async_requests_mode"}
_INT_KEYS: set[str] = set()

_SAMPLE_CONFIG = """\
[DEFAULT]
ssl = True
verify = True
namespace = LDAP
async_requests_mode = True

; Add one section per TM1 server. The section name is passed as <tm1> on the command line.
; base_url format: https://<hostname>.planning-analytics.ibmcloud.com/tm1/api/<database_folder>/
[my_paoc_server]
base_url = https://myinstance.planning-analytics.ibmcloud.com/tm1/api/my_database/
user = myuser@example.com
password = changeme
namespace = LDAP
encrypted = no
"""


def _hide_file(path: str) -> None:
    if sys.platform == "win32":
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)


def _load_or_create_key(key_path: str) -> bytes:
    resolved = os.path.abspath(key_path)
    if os.path.isfile(resolved):
        with open(resolved, "rb") as f:
            return f.read().strip()
    key = Fernet.generate_key()
    with open(resolved, "wb") as f:
        f.write(key)
    _hide_file(resolved)
    log.info("Generated new encryption key at: %s", resolved)
    return key


def _create_sample_config(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(_SAMPLE_CONFIG)
    log.warning("No config file found. Created sample config at: %s", path)
    log.warning("Edit it with your TM1 server details, then re-run.")


def _encrypt_section_password(config_path: str, key_path: str, section_name: str) -> None:
    """Encrypt the password for a single section and flip its encrypted = yes."""
    key = _load_or_create_key(key_path)
    fernet = Fernet(key)

    config = configparser.ConfigParser()
    config.read(os.path.abspath(config_path))

    plain = config[section_name]["password"]
    config[section_name]["password"] = fernet.encrypt(plain.encode()).decode()
    config[section_name]["encrypted"] = "yes"

    with open(os.path.abspath(config_path), "w") as f:
        config.write(f)

    log.info("Password encrypted for server '%s'.", section_name)


def get_tm1_connection(server_name: str, config_path: str = _DEFAULT_CONFIG_PATH,
                       key_path: str = _DEFAULT_KEY_PATH) -> dict[str, Any]:
    resolved = os.path.abspath(config_path)

    if not os.path.isfile(resolved):
        _create_sample_config(resolved)
        raise FileNotFoundError(f"Config file not found: {resolved}")

    # Encrypt this section's password on first run if its flag is 'no'
    raw = configparser.ConfigParser()
    raw.read(resolved)
    if server_name not in raw:
        available = raw.sections()
        raise KeyError(f"Server '{server_name}' not found in config. Available: {available}")
    if raw[server_name].get("encrypted", "no").strip().lower() == "no":
        log.info("Password for '%s' is unencrypted — encrypting now.", server_name)
        _encrypt_section_password(resolved, key_path, server_name)

    log.debug("Reading config from: %s", resolved)
    config = configparser.ConfigParser()
    config.read(resolved)

    key = _load_or_create_key(os.path.abspath(key_path))
    fernet = Fernet(key)

    section = config[server_name]
    connection: dict[str, Any] = {}

    for k, value in section.items():
        if k == "encrypted":
            continue
        elif k in _BOOL_KEYS:
            connection[k] = section.getboolean(k)
        elif k in _INT_KEYS:
            connection[k] = section.getint(k)
        elif k == "password":
            connection[k] = fernet.decrypt(value.encode()).decode()
        else:
            connection[k] = value

    log.debug("Loaded connection config for server '%s'", server_name)
    return connection
