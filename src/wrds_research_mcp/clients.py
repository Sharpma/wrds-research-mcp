from __future__ import annotations

from typing import Protocol

from wrds_research_mcp.models import QueryPlan, ResearchRequest, SecurityIdentifier
from wrds_research_mcp.wrds_connection import run_wrds_operation, _wrds_connection_kwargs


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

    def fetch_returns(
        self,
        request: ResearchRequest,
        security: SecurityIdentifier,
        query_plan: QueryPlan,
    ) -> list[dict]:
        dataframe = run_wrds_operation(
            lambda db: db.raw_sql(
                query_plan.sql,
                params=query_plan.params,
                date_cols=["date"],
            )
        )
        dataframe["company_name"] = security.company_name
        dataframe["source"] = self.source
        return dataframe.to_dict("records")


def get_data_client(source: str) -> DataClient:
    normalized = source.lower()
    if normalized == "wrds":
        return WRDSCRSPClient()
    raise ValueError("source must be 'wrds'.")
