from __future__ import annotations

from contextlib import redirect_stdout
import io
from typing import Any

from wrds_research_mcp.clients import _wrds_connection_kwargs


def connect_wrds_quietly() -> Any:
    try:
        import wrds
    except ImportError as exc:
        raise RuntimeError("Install WRDS support with: uv sync --extra wrds") from exc

    with redirect_stdout(io.StringIO()):
        return wrds.Connection(**_wrds_connection_kwargs())
