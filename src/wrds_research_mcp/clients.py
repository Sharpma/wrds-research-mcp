from __future__ import annotations

from datetime import date, timedelta
import os
from pathlib import Path
from typing import Protocol

from wrds_research_mcp.models import QueryPlan, ResearchRequest, SecurityIdentifier


class DataClient(Protocol):
    def fetch_daily_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
        query_plan: QueryPlan,
    ) -> list[dict]:
        ...


class MockCRSPClient:
    source = "mock"

    def fetch_daily_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
        query_plan: QueryPlan,
    ) -> list[dict]:
        rows = []
        price = 188.0

        for idx, current_date in enumerate(_business_days(request.start_date, request.end_date)):
            daily_return = round(((idx % 7) - 3) * 0.0025, 6)
            price = round(price * (1 + daily_return), 2)
            rows.append(
                {
                    "date": current_date,
                    "permno": security.permno,
                    "ticker": security.ticker,
                    "company_name": security.company_name,
                    "ret": daily_return,
                    "retx": daily_return,
                    "prc": price,
                    "vol": 50_000_000 + idx * 137_000,
                    "source": self.source,
                }
            )

        return rows


class WRDSCRSPClient:
    source = "wrds"

    def __init__(self) -> None:
        try:
            import wrds
        except ImportError as exc:
            raise RuntimeError("Install WRDS support with: uv sync --extra wrds") from exc

        self.connection = wrds.Connection(**_wrds_connection_kwargs())

    def fetch_daily_returns(
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
    if normalized == "mock":
        return MockCRSPClient()
    if normalized == "wrds":
        return WRDSCRSPClient()
    raise ValueError("source must be either 'mock' or 'wrds'.")


def _wrds_connection_kwargs() -> dict[str, str]:
    username = (
        os.environ.get("WRDS_USERNAME")
        or os.environ.get("WRDS_USER")
        or os.environ.get("PGUSER")
    )
    password = (
        os.environ.get("WRDS_PASSWORD")
        or os.environ.get("WRDS_PASS")
        or os.environ.get("PGPASSWORD")
    )

    if not username:
        raise RuntimeError(
            "WRDS username is not configured. Set WRDS_USERNAME or PGUSER before "
            "using the wrds_readonly profile."
        )

    kwargs = {"wrds_username": username}
    if password:
        kwargs["wrds_password"] = password
        return kwargs

    if _pgpass_exists():
        return kwargs

    raise RuntimeError(
        "WRDS password is not configured. Set WRDS_PASSWORD/PGPASSWORD, or set "
        "WRDS_USERNAME and configure a local pgpass file. Do not send WRDS "
        "passwords through chat."
    )


def _pgpass_exists() -> bool:
    candidates = [
        Path.home() / ".pgpass",
        Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf",
        Path.home() / ".pg_service.conf",
    ]
    return any(path.exists() for path in candidates)


def _business_days(start_date: date, end_date: date) -> list[date]:
    holidays = _demo_market_holidays(start_date.year) | _demo_market_holidays(end_date.year)
    current_date = start_date
    days = []
    while current_date <= end_date:
        if current_date.weekday() < 5 and current_date not in holidays:
            days.append(current_date)
        current_date += timedelta(days=1)
    return days


def _demo_market_holidays(year: int) -> set[date]:
    if year == 2025:
        return {date(2025, 1, 1), date(2025, 1, 20)}
    return set()
