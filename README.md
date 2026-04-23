# RemoteProcess

**Version 2.0.0.4** — © 2026 Application Consulting Group, Inc.

Execute IBM Planning Analytics (TM1) processes remotely from the command line or from a TM1 TurboIntegrator process via `ExecuteCommand`.

---

## Requirements

- Python 3.11+
- IBM Planning Analytics / TM1 server reachable over HTTPS

**pip:**
```
pip install -r requirements.txt
```

**conda:**
```
conda env create -f environment.yml
conda activate remoteexecute
```

---

## Installation

1. Copy `RemoteProcess.exe` (or the Python source) and `config.ini` to a folder on the target machine.
2. Edit `config.ini` to add your TM1 server(s) — see [Configuration](#configuration) below.
3. Run once to encrypt passwords automatically.

---

## Usage

```
RemoteProcess.exe <tm1> <process> <parameters>
RemoteProcess.exe --help
RemoteProcess.exe --version
```

| Argument | Description |
|---|---|
| `<tm1>` | Server name — must match a section header in `config.ini` |
| `<process>` | TM1 process name exactly as it appears in the model |
| `<parameters>` | Semicolon-separated `key=value` pairs, e.g. `"pPeriod=2025-01;pEntity=US"` |

Numeric values are coerced automatically (integer → float → string).

### Examples

```
# No parameters
RemoteProcess.exe prod_server "}Stats.ExportToLog" ""

# Single parameter
RemoteProcess.exe prod_server "LoadData.Account" "pPeriod=2025-01"

# Multiple parameters
RemoteProcess.exe prod_server "LoadData.Account" "pPeriod=2025-01;pEntity=US;pReload=1"
```

### Calling from a TI process

```
sCmdPath = 'C:\Apps\RemoteProcess\RemoteProcess.exe';
sServer   = 'prod_server';
sProcess  = 'LoadData.Account';
sParams   = 'pPeriod=' | pPeriod | ';pEntity=' | pEntity | ';pReload=' | NumberToString(pReload);
sCommand  = sCmdPath | ' ' | sServer | ' "' | sProcess | '" "' | sParams | '"';

ExecuteCommand(sCommand, 1);  # 1 = wait for completion
```

---

## Configuration

Connections are defined in `config.ini` in the same directory as the executable.

```ini
[DEFAULT]
ssl                = True
verify             = True
namespace          = LDAP
async_requests_mode = True

[prod_server]
base_url  = https://myinstance.planning-analytics.ibmcloud.com/tm1/api/my_database/
user      = myuser@example.com
password  = changeme
namespace = LDAP
encrypted = no

[dev_server]
base_url  = https://devinstance.planning-analytics.ibmcloud.com/tm1/api/dev_database/
user      = myuser@example.com
password  = changeme
namespace = LDAP
encrypted = no
```

The `encrypted` flag is **per server section**:

| Value | Behaviour |
|---|---|
| `no` | Password is plain text. On first use the password is encrypted in-place and the flag is flipped to `yes`. |
| `yes` | Password is Fernet-encrypted. Decrypted in memory at runtime only. |

Adding a new server with `encrypted = no` does not affect existing entries.

### secret.key

Passwords are encrypted with [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption. The key is stored in `secret.key` alongside `config.ini`.

- Generated automatically on first run if it does not exist.
- The file is marked **hidden** on Windows.
- **Back up `secret.key` with `config.ini`.** Losing the key makes all encrypted passwords unrecoverable.
- **Never commit `secret.key` to source control** — add it to `.gitignore`.

---

## Building the executable

```
python app_build.py
```

Produces `RemoteProcess.exe` via PyInstaller. Distribute the `.exe` and `config.ini` together; `secret.key` is generated on first run on the target machine.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Process completed successfully |
| `1` | Invalid parameters, config error, or process failure |
