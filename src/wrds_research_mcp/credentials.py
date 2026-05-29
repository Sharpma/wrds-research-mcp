from __future__ import annotations

from contextlib import redirect_stdout
import getpass
import io
import os
from pathlib import Path
from typing import Any


WRDS_HOST = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT = "9737"
WRDS_DB = "wrds"


def pgpass_path() -> Path:
    override = os.environ.get("PGPASSFILE")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "postgresql" / "pgpass.conf"
        return Path.home() / "AppData" / "Roaming" / "postgresql" / "pgpass.conf"

    return Path.home() / ".pgpass"


def setup_wrds_credentials(
    username: str,
    password: str,
    path: str | Path | None = None,
) -> Path:
    if not username.strip():
        raise ValueError("WRDS username must not be empty.")
    if not password:
        raise ValueError("WRDS password must not be empty.")

    target = Path(path).expanduser() if path else pgpass_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    new_line = _pgpass_line(username.strip(), password)
    existing_lines = _read_pgpass_lines(target)
    retained_lines = [
        line
        for line in existing_lines
        if not _is_wrds_pgpass_line(line)
    ]
    retained_lines.append(new_line)
    target.write_text("\n".join(retained_lines) + "\n", encoding="utf-8")

    if os.name != "nt":
        target.chmod(0o600)

    return target


def prompt_and_setup_wrds_credentials(
    username: str | None = None,
    path: str | Path | None = None,
    test_connection: bool = True,
) -> dict[str, Any]:
    selected_username = (username or input("WRDS username: ")).strip()
    password = getpass.getpass("WRDS password: ")
    target = setup_wrds_credentials(selected_username, password, path)

    connection_test = {"attempted": False, "ok": None, "message": "skipped"}
    if test_connection:
        connection_test = test_wrds_credentials(selected_username)

    return {
        "pgpass_path": str(target),
        "username": selected_username,
        "connection_test": connection_test,
    }


def find_wrds_username_in_pgpass(path: str | Path | None = None) -> str | None:
    target = Path(path).expanduser() if path else pgpass_path()
    for line in _read_pgpass_lines(target):
        parts = _split_pgpass_line(line)
        if len(parts) != 5:
            continue
        host, port, database, username, _password = parts
        if _matches_wrds_entry(host, port, database) and username:
            return _unescape_pgpass_value(username)
    return None


def wrds_pgpass_exists(path: str | Path | None = None) -> bool:
    target = Path(path).expanduser() if path else pgpass_path()
    if not target.exists():
        return False
    return find_wrds_username_in_pgpass(target) is not None


def test_wrds_credentials(username: str) -> dict[str, Any]:
    try:
        import wrds
    except ImportError:
        return {
            "attempted": True,
            "ok": False,
            "message": "Install WRDS support with: uv sync --extra wrds",
        }

    try:
        with redirect_stdout(io.StringIO()):
            connection = wrds.Connection(wrds_username=username)
        close = getattr(connection, "close", None)
        if callable(close):
            close()
    except Exception as exc:
        return {
            "attempted": True,
            "ok": False,
            "message": f"{type(exc).__name__}: {exc}",
        }

    return {
        "attempted": True,
        "ok": True,
        "message": "WRDS connection succeeded.",
    }


def _pgpass_line(username: str, password: str) -> str:
    return ":".join(
        [
            WRDS_HOST,
            WRDS_PORT,
            WRDS_DB,
            _escape_pgpass_value(username),
            _escape_pgpass_value(password),
        ]
    )


def _read_pgpass_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _is_wrds_pgpass_line(line: str) -> bool:
    parts = _split_pgpass_line(line)
    if len(parts) != 5:
        return False
    host, port, database, _username, _password = parts
    return _matches_wrds_entry(host, port, database)


def _matches_wrds_entry(host: str, port: str, database: str) -> bool:
    return (
        _unescape_pgpass_value(host) in {WRDS_HOST, "*"}
        and _unescape_pgpass_value(port) in {WRDS_PORT, "*"}
        and _unescape_pgpass_value(database) in {WRDS_DB, "*"}
    )


def _escape_pgpass_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:")


def _unescape_pgpass_value(value: str) -> str:
    output = []
    escaped = False
    for char in value:
        if escaped:
            output.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        else:
            output.append(char)
    if escaped:
        output.append("\\")
    return "".join(output)


def _split_pgpass_line(line: str) -> list[str]:
    parts = []
    current = []
    escaped = False
    for char in line:
        if escaped:
            current.append("\\" + char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    parts.append("".join(current))
    return parts
