from __future__ import annotations

from pathlib import Path
from typing import Any

from wrds_research_mcp.catalog import CATALOG
from wrds_research_mcp.identifiers import resolve_security_identifier
from wrds_research_mcp.nlp import parse_research_request
from wrds_research_mcp.policy import (
    get_dataset_policy,
    get_permission_profile,
    load_policy_document,
    validate_query_policy,
    validate_request_policy,
)
from wrds_research_mcp.query import build_query_plan


CURATED_WORKFLOW_SCOPE_NOTE = (
    "These are curated high-confidence research workflows, not the full WRDS database "
    "catalog. For broader data requests, use live library discovery tools."
)


def list_permission_profiles(policy_path: str | Path | None = None) -> dict[str, Any]:
    document = load_policy_document(policy_path)
    profiles = {}
    for name in sorted(document["profiles"]):
        profile = get_permission_profile(document, name)
        profiles[name] = {
            "description": profile.description,
            "source": profile.source,
            "allowed_curated_workflows": profile.allowed_datasets,
            "max_date_span_days": profile.max_date_span_days,
            "max_rows": profile.max_rows,
            "max_generic_rows": profile.max_generic_rows,
            "output_root": profile.output_root,
            "allow_raw_sql": profile.allow_raw_sql,
            "allowed_libraries": profile.allowed_libraries,
            "blocked_libraries": profile.blocked_libraries,
        }
    return {"profiles": profiles}


def list_datasets(
    profile: str = "wrds_readonly",
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(document, profile)
    workflows = {}
    for dataset_name in permission_profile.allowed_datasets:
        dataset_policy = get_dataset_policy(document, dataset_name)
        catalog_entry = CATALOG.get(dataset_name, {})
        workflows[dataset_name] = {
            "kind": "curated_research_workflow",
            "label": catalog_entry.get("label", dataset_name),
            "description": dataset_policy.description,
            "frequency": catalog_entry.get("frequency"),
            "tables": dataset_policy.tables,
            "allowed_fields": dataset_policy.allowed_fields,
            "required_filters": dataset_policy.required_filters,
            "allowed_output_formats": dataset_policy.allowed_output_formats,
            "allowed_query_templates": dataset_policy.allowed_query_templates,
        }
    return {
        "profile": profile,
        "catalog_scope": "curated_research_workflows_only",
        "scope_note": CURATED_WORKFLOW_SCOPE_NOTE,
        "workflow_count": len(workflows),
        "curated_research_workflows": workflows,
        "datasets": workflows,
        "broader_wrds_discovery_tools": [
            "search_accessible_wrds_libraries",
            "list_accessible_wrds_libraries",
            "describe_accessible_wrds_library",
            "list_accessible_wrds_tables",
            "describe_accessible_wrds_table",
            "materialize_accessible_wrds_table",
        ],
    }


def get_dataset_contract(
    dataset: str,
    profile: str = "wrds_readonly",
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(document, profile)
    if dataset not in permission_profile.allowed_datasets:
        raise ValueError(f"Dataset {dataset!r} is not allowed by profile {profile!r}.")

    dataset_policy = get_dataset_policy(document, dataset)
    catalog_entry = CATALOG.get(dataset, {})
    return {
        "kind": "curated_research_workflow",
        "scope_note": CURATED_WORKFLOW_SCOPE_NOTE,
        "profile": profile,
        "dataset": dataset,
        "label": catalog_entry.get("label", dataset),
        "frequency": catalog_entry.get("frequency"),
        "identifiers": catalog_entry.get("identifiers", []),
        "tables": dataset_policy.tables,
        "fields": catalog_entry.get("fields", {}),
        "allowed_fields": dataset_policy.allowed_fields,
        "required_filters": dataset_policy.required_filters,
        "allowed_output_formats": dataset_policy.allowed_output_formats,
        "allowed_query_templates": dataset_policy.allowed_query_templates,
        "limits": {
            "max_date_span_days": permission_profile.max_date_span_days,
            "max_rows": permission_profile.max_rows,
            "output_root": permission_profile.output_root,
        },
        "execution_tool": "get_research_data",
        "broader_wrds_discovery_tools": [
            "search_accessible_wrds_libraries",
            "list_accessible_wrds_libraries",
            "describe_accessible_wrds_library",
            "list_accessible_wrds_tables",
            "describe_accessible_wrds_table",
            "materialize_accessible_wrds_table",
        ],
    }


def plan_research_request(
    request: str,
    profile: str = "wrds_readonly",
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(document, profile)
    parsed_request = parse_research_request(request)
    dataset_policy = get_dataset_policy(document, parsed_request.dataset)
    validate_request_policy(parsed_request, permission_profile, dataset_policy)

    security = resolve_security_identifier(parsed_request)
    query_plan = build_query_plan(parsed_request, security, permission_profile.max_rows)
    validate_query_policy(query_plan, permission_profile, dataset_policy)

    return {
        "profile": profile,
        "source": permission_profile.source,
        "request": parsed_request.as_dict(),
        "security": security.as_dict(),
        "dataset_contract": get_dataset_contract(parsed_request.dataset, profile, policy_path),
        "query_plan": query_plan.as_dict(),
        "next_step": {
            "tool": "get_research_data",
            "arguments": {
                "request": request,
                "profile": profile,
            },
        },
    }
