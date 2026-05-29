from __future__ import annotations

from pathlib import Path

from wrds_research_mcp.clients import get_data_client
from wrds_research_mcp.identifiers import resolve_security_identifier
from wrds_research_mcp.models import PipelineResult
from wrds_research_mcp.nlp import parse_research_request
from wrds_research_mcp.policy import (
    enforce_row_limit,
    get_dataset_policy,
    get_permission_profile,
    load_policy_document,
    resolve_output_dir,
    validate_query_policy,
    validate_request_policy,
    validate_source,
)
from wrds_research_mcp.query import build_query_plan
from wrds_research_mcp.writers import write_parquet_dataset


def run_research_request(
    text: str,
    output_dir: str | Path | None = None,
    source: str | None = None,
    profile: str = "demo",
    policy_path: str | Path | None = None,
) -> PipelineResult:
    policy_document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(policy_document, profile)
    selected_source = source or permission_profile.source
    validate_source(selected_source, permission_profile)
    selected_output_dir = resolve_output_dir(output_dir, permission_profile)

    request = parse_research_request(text)
    dataset_policy = get_dataset_policy(policy_document, request.dataset)
    validate_request_policy(request, permission_profile, dataset_policy)

    security = resolve_security_identifier(request)
    query_plan = build_query_plan(request, security, permission_profile.max_rows)
    validate_query_policy(query_plan, permission_profile, dataset_policy)

    client = get_data_client(selected_source)
    rows = client.fetch_returns(request, security, query_plan)
    enforce_row_limit(len(rows), permission_profile)
    dataset = write_parquet_dataset(
        rows,
        selected_output_dir,
        request,
        security,
        query_plan,
        selected_source,
        permission_profile.name,
    )

    return PipelineResult(
        request=request,
        security=security,
        query_plan=query_plan,
        dataset=dataset,
        source=selected_source,
        permission_profile=permission_profile.name,
    )
