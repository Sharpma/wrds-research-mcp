from __future__ import annotations

from contextlib import redirect_stdout
import io
import os
from typing import Protocol

from wrds_research_mcp.credentials import find_wrds_username_in_pgpass, wrds_pgpass_exists
from wrds_research_mcp.models import QueryPlan, ResearchRequest, SecurityIdentifier


class DataClient(Protocol):
    def fetch_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
        query_plan: QueryPlan,
    ) -> list[dict]:
        ...


class WRDSCRSPClient:
    source = "wrds"

    def __init__(self) -> None:
        try:
            import wrds
        except ImportError as exc:
            raise RuntimeError(
                "Install WRDS support with: pip install 'wrds-research-mcp[wrds]' "
                "or uv sync --extra wrds"
            ) from exc

        with redirect_stdout(io.StringIO()):
            self.connection = wrds.Connection(**_wrds_connection_kwargs())

    def fetch_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
        query_plan: QueryPlan,
    ) -> list[dict]:
        dataframe = self.connection.raw_sql(
            query_plan.sql,
            params=query_plan.params,
            date_cols=["date"],
        )
        dataframe["company_name"] = security.company_name
        dataframe["source"] = self.source
        return dataframe.to_dict("records")


def get_data_client(source: str) -> DataClient:
    normalized = source.lower()
    if normalized == "wrds":
        return WRDSCRSPClient()
    raise ValueError("source must be 'wrds'.")


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
