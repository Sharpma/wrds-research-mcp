from __future__ import annotations

from contextlib import redirect_stdout
import io
import os
import time
from typing import Any, Callable, TypeVar

from wrds_research_mcp.credentials import find_wrds_username_in_pgpass, wrds_pgpass_exists


T = TypeVar("T")

DEFAULT_MAX_ATTEMPTS = 2
TRANSIENT_CLASS_NAMES = {
    "OperationalError",
    "InterfaceError",
}
TRANSIENT_MESSAGE_PATTERNS = (
    "server closed the connection unexpectedly",
    "connection already closed",
    "connection not open",
    "closed cursor",
    "ssl syscall error",
    "eof detected",
    "terminating connection",
    "could not receive data from server",
    "could not send data to server",
    "connection reset by peer",
    "broken pipe",
)
NON_RETRYABLE_MESSAGE_PATTERNS = (
    "password authentication failed",
    "authentication failed",
    "permission denied",
    "undefinedcolumn",
    "undefinedtable",
    "syntax error",
)


def connect_wrds_quietly() -> Any:
    try:
        import wrds
    except ImportError as exc:
        raise RuntimeError(
            "Install WRDS support with: pip install 'wrds-research-mcp[wrds]' "
            "or uv sync --extra wrds"
        ) from exc

    with redirect_stdout(io.StringIO()):
        return wrds.Connection(**_wrds_connection_kwargs())


def run_wrds_operation(
    operation: Callable[[Any], T],
    max_attempts: int | None = None,
) -> T:
    attempts = max(1, max_attempts or _configured_max_attempts())
    last_error: Exception | None = None

    for attempt_index in range(attempts):
        connection = None
        try:
            connection = connect_wrds_quietly()
            return operation(connection)
        except Exception as exc:
            last_error = exc
            if attempt_index >= attempts - 1 or not is_transient_wrds_error(exc):
                raise
            time.sleep(min(0.5 * (attempt_index + 1), 2.0))
        finally:
            if connection is not None:
                close_wrds_connection(connection)

    raise RuntimeError("WRDS operation failed after retry.") from last_error


def close_wrds_connection(connection: Any) -> None:
    close = getattr(connection, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def is_transient_wrds_error(exc: BaseException) -> bool:
    message = _exception_chain_message(exc)
    if any(pattern in message for pattern in NON_RETRYABLE_MESSAGE_PATTERNS):
        return False
    if any(pattern in message for pattern in TRANSIENT_MESSAGE_PATTERNS):
        return True

    current: BaseException | None = exc
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if type(current).__name__ in TRANSIENT_CLASS_NAMES:
            return True
        current = current.__cause__ or current.__context__
    return False


def _wrds_connection_kwargs() -> dict[str, str]:
    username = (
        os.environ.get("WRDS_USERNAME")
        or os.environ.get("WRDS_USER")
        or os.environ.get("PGUSER")
        or find_wrds_username_in_pgpass()
    )
    password = (
        os.environ.get("WRDS_PASSWORD")
        or os.environ.get("WRDS_PASS")
        or os.environ.get("PGPASSWORD")
    )

    if not username:
        raise RuntimeError(
            "WRDS username is not configured. Run wrds-research-setup first, "
            "or set WRDS_USERNAME/PGUSER before using the wrds_readonly profile."
        )

    kwargs = {"wrds_username": username}
    if password:
        kwargs["wrds_password"] = password
        return kwargs

    if wrds_pgpass_exists():
        return kwargs

    raise RuntimeError(
        "WRDS password is not configured. Run wrds-research-setup first, or set "
        "WRDS_PASSWORD/PGPASSWORD. Do not send WRDS passwords through chat."
    )


def _configured_max_attempts() -> int:
    raw_value = os.environ.get("WRDS_RESEARCH_MCP_DB_ATTEMPTS")
    if not raw_value:
        return DEFAULT_MAX_ATTEMPTS
    try:
        return int(raw_value)
    except ValueError:
        return DEFAULT_MAX_ATTEMPTS


def _exception_chain_message(exc: BaseException) -> str:
    messages = []
    current: BaseException | None = exc
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        messages.append(str(current))
        current = current.__cause__ or current.__context__
    return "\n".join(messages).lower()
