from __future__ import annotations

from pathlib import Path

from wrds_research_mcp.clients import get_data_client
from wrds_research_mcp.identifiers import resolve_security_identifier
from wrds_research_mcp.models import PipelineResult
from wrds_research_mcp.nlp import parse_research_request
from wrds_research_mcp.query import build_crsp_daily_returns_query
from wrds_research_mcp.writers import write_parquet_dataset


def run_research_request(
    text: str,
    output_dir: str | Path = "data/demo",
    source: str = "mock",
) -> PipelineResult:
    request = parse_research_request(text)
    security = resolve_security_identifier(request)
    query_plan = build_crsp_daily_returns_query(request, security)
    client = get_data_client(source)
    rows = client.fetch_daily_returns(request, security, query_plan)
    dataset = write_parquet_dataset(rows, output_dir, request, security, query_plan, source)

    return PipelineResult(
        request=request,
        security=security,
        query_plan=query_plan,
        dataset=dataset,
        source=source,
    )
