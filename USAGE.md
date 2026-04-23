# RemoteProcess — Usage Examples

## Syntax

```
RemoteProcess.exe <tm1> <process> <parameters>
```

| Argument | Description |
|---|---|
| `<tm1>` | Server name matching a section header in `config.ini` |
| `<process>` | TM1 process name exactly as it appears in the model |
| `<parameters>` | Semicolon-separated `key=value` pairs — no quotes required |

Parameters format: `pParam1=value1;pParam2=42;pParam3=3.14`

Numeric values are coerced automatically (integer, then float, then string).

---

## Help and version

```
RemoteProcess.exe --help
RemoteProcess.exe --version
```

---

## No parameters

Pass an empty string when the process takes no parameters.

```
RemoteProcess.exe prod_server "}Stats.ExportToLog" ""
```

---

## Single parameter

```
RemoteProcess.exe prod_server "LoadData.Account" "pPeriod=2025-01"
```

---

## Multiple parameters

```
RemoteProcess.exe prod_server "LoadData.Account" "pPeriod=2025-01;pEntity=US;pReload=1"
```

---

## Numeric parameters

Integers and floats are coerced automatically — no special syntax needed.

```
RemoteProcess.exe prod_server "Archive.Cube" "pYear=2024;pDeleteSource=1"
```

---

## Calling from a TM1 TI process

Build the parameter string with string concatenation and call `ExecuteCommand`.
No quoting tricks are needed because the format contains no double quotes.

Wrap both `<process>` and `<parameters>` in double quotes so that spaces in
process names or parameter values are passed through correctly.

```
# TurboIntegrator code

sCmdPath = 'C:\Apps\RemoteProcess\RemoteProcess.exe';
sServer   = 'prod_server';
sProcess  = 'LoadData.Account';

# Spaces in values (e.g. "North America") are safe — the outer quotes protect them
sParams = 'pPeriod=' | pPeriod | ';pEntity=' | pEntity | ';pReload=' | NumberToString(pReload);

# Both process name and params are wrapped in double quotes
sCommand = sCmdPath | ' ' | sServer | ' "' | sProcess | '" "' | sParams | '"';

ExecuteCommand(sCommand, 1);  # 1 = wait for completion
```

> **Note:** `value.strip()` trims only leading/trailing whitespace from each value.
> An embedded space such as `pEntity=North America` is preserved as-is.

---

## Setup

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

## Running as a Python script (development)

```
python src/RemoteProcess.py prod_server "LoadData.Account" "pPeriod=2025-01;pEntity=US"
```

---

## config.ini server names

The `<tm1>` argument must match a section header in `config.ini`.

Each server section requires an `encrypted` flag:

- `encrypted = no` — password is stored as plain text; it will be encrypted automatically on the first run that uses this server, and the flag will be flipped to `yes`
- `encrypted = yes` — password is already encrypted; it is decrypted in memory at runtime and never written back as plain text

```ini
[prod_server]
base_url = https://myinstance.planning-analytics.ibmcloud.com/tm1/api/my_database/
user = myuser@example.com
password = changeme
namespace = LDAP
encrypted = no

[dev_server]
base_url = https://devinstance.planning-analytics.ibmcloud.com/tm1/api/dev_database/
user = myuser@example.com
password = changeme
namespace = LDAP
encrypted = no
```

### secret.key

Passwords are encrypted with [Fernet](https://cryptography.io/en/latest/fernet/) symmetric encryption.
The key is stored in `secret.key` in the same directory as `config.ini`.

- If `secret.key` does not exist it is generated automatically on first run.
- **Back up `secret.key` alongside `config.ini`.** Losing the key makes encrypted passwords unrecoverable.
- **Do not commit `secret.key` to source control.** Add it to `.gitignore`.
- The `encrypted` flag is per-server, so you can add new servers with `encrypted = no` without affecting existing entries.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Process completed successfully |
| `1` | Invalid parameters, config error, or process failure |
