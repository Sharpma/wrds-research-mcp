from __future__ import annotations

from contextlib import redirect_stdout
from datetime import date, timedelta
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


class MockCRSPClient:
    source = "mock"

    def fetch_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
        query_plan: QueryPlan,
    ) -> list[dict]:
        if request.frequency == "monthly":
            return self._fetch_monthly_returns(request, security)

        return self._fetch_daily_returns(request, security)

    def _fetch_daily_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
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

    def _fetch_monthly_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
    ) -> list[dict]:
        rows = []
        price = 188.0

        current = date(request.start_date.year, request.start_date.month, 1)
        while current <= request.end_date:
            month_end = _month_end(current)
            if month_end >= request.start_date:
                monthly_return = round(((current.month % 7) - 3) * 0.015, 6)
                price = round(price * (1 + monthly_return), 2)
                rows.append(
                    {
                        "date": month_end,
                        "permno": security.permno,
                        "ticker": security.ticker,
                        "company_name": security.company_name,
                        "ret": monthly_return,
                        "retx": monthly_return,
                        "prc": price,
                        "vol": 1_000_000_000 + current.month * 10_000_000,
                        "source": self.source,
                    }
                )
            current = _next_month(current)

        return rows


class WRDSCRSPClient:
    source = "wrds"

    def __init__(self) -> None:
        try:
            import wrds
        except ImportError as exc:
            raise RuntimeError("Install WRDS support with: uv sync --extra wrds") from exc

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


def _month_end(day: date) -> date:
    next_month = _next_month(day)
    return next_month - timedelta(days=1)


def _next_month(day: date) -> date:
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)
