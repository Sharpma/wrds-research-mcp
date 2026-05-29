from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from wrds_research_mcp.models import QueryPlan, ResearchRequest


DEFAULT_POLICY_PATH = Path("config/permissions.yaml")

TABLE_REF_RE = re.compile(r"\b(?:from|join)\s+([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)", re.IGNORECASE)
FORBIDDEN_SQL_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|call|execute)\b",
    re.IGNORECASE,
)


class PolicyViolation(ValueError):
    """Raised when a request violates the configured MCP data policy."""


@dataclass(frozen=True)
class PermissionProfile:
    name: str
    source: str
    allowed_datasets: list[str]
    max_date_span_days: int
    max_rows: int
    output_root: str
    allow_raw_sql: bool
    description: str = ""


@dataclass(frozen=True)
class DatasetPolicy:
    name: str
    tables: list[str]
    allowed_fields: list[str]
    required_filters: list[str]
    allowed_frequencies: list[str]
    allowed_output_formats: list[str]
    allowed_query_templates: list[str]
    description: str = ""


def load_policy_document(policy_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(policy_path) if policy_path else DEFAULT_POLICY_PATH
    if not path.exists():
        raise FileNotFoundError(f"Permission policy file not found: {path}")

    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(document, dict):
        raise PolicyViolation("Permission policy must be a mapping.")
    if "profiles" not in document or "datasets" not in document:
        raise PolicyViolation("Permission policy must define profiles and datasets.")
    return document


def get_permission_profile(document: dict[str, Any], profile_name: str) -> PermissionProfile:
    raw_profiles = document.get("profiles", {})
    raw_profile = raw_profiles.get(profile_name)
    if not isinstance(raw_profile, dict):
        raise PolicyViolation(f"Unknown permission profile: {profile_name}")

    return PermissionProfile(
        name=profile_name,
        source=str(raw_profile["source"]),
        allowed_datasets=list(raw_profile.get("allowed_datasets", [])),
        max_date_span_days=int(raw_profile["max_date_span_days"]),
        max_rows=int(raw_profile["max_rows"]),
        output_root=str(raw_profile["output_root"]),
        allow_raw_sql=bool(raw_profile.get("allow_raw_sql", False)),
        description=str(raw_profile.get("description", "")),
    )


def get_dataset_policy(document: dict[str, Any], dataset_name: str) -> DatasetPolicy:
    raw_datasets = document.get("datasets", {})
    raw_dataset = raw_datasets.get(dataset_name)
    if not isinstance(raw_dataset, dict):
        raise PolicyViolation(f"Unknown dataset policy: {dataset_name}")

    return DatasetPolicy(
        name=dataset_name,
        tables=list(raw_dataset.get("tables", [])),
        allowed_fields=list(raw_dataset.get("allowed_fields", [])),
        required_filters=list(raw_dataset.get("required_filters", [])),
        allowed_frequencies=list(raw_dataset.get("allowed_frequencies", [])),
        allowed_output_formats=list(raw_dataset.get("allowed_output_formats", [])),
        allowed_query_templates=list(raw_dataset.get("allowed_query_templates", [])),
        description=str(raw_dataset.get("description", "")),
    )


def validate_source(source: str, profile: PermissionProfile) -> None:
    if source != profile.source:
        raise PolicyViolation(
            f"Source {source!r} is not allowed by profile {profile.name!r}; "
            f"expected {profile.source!r}."
        )


def validate_request_policy(
    request: ResearchRequest,
    profile: PermissionProfile,
    dataset_policy: DatasetPolicy,
) -> None:
    if request.dataset not in profile.allowed_datasets:
        raise PolicyViolation(
            f"Dataset {request.dataset!r} is not allowed by profile {profile.name!r}."
        )

    if request.dataset != dataset_policy.name:
        raise PolicyViolation("Request dataset and dataset policy do not match.")

    date_span_days = (request.end_date - request.start_date).days + 1
    if date_span_days <= 0:
        raise PolicyViolation("Date range must be non-empty and ordered.")
    if date_span_days > profile.max_date_span_days:
        raise PolicyViolation(
            f"Date range spans {date_span_days} days; profile limit is "
            f"{profile.max_date_span_days} days."
        )

    if request.frequency not in dataset_policy.allowed_frequencies:
        raise PolicyViolation(f"Frequency {request.frequency!r} is not allowed.")

    if request.output_format not in dataset_policy.allowed_output_formats:
        raise PolicyViolation(f"Output format {request.output_format!r} is not allowed.")

    disallowed_fields = sorted(set(request.fields) - set(dataset_policy.allowed_fields))
    if disallowed_fields:
        raise PolicyViolation(f"Fields are not allowed: {', '.join(disallowed_fields)}")

    if "date_range" in dataset_policy.required_filters and not (
        request.start_date and request.end_date
    ):
        raise PolicyViolation("Dataset requires a date range filter.")

    if "security_identifier" in dataset_policy.required_filters and not request.ticker:
        raise PolicyViolation("Dataset requires a security identifier filter.")


def validate_query_policy(
    query_plan: QueryPlan,
    profile: PermissionProfile,
    dataset_policy: DatasetPolicy,
) -> None:
    if query_plan.dataset != dataset_policy.name:
        raise PolicyViolation("Query plan dataset and dataset policy do not match.")

    if query_plan.template_id not in dataset_policy.allowed_query_templates:
        raise PolicyViolation(f"Query template {query_plan.template_id!r} is not allowed.")

    unexpected_tables = sorted(set(query_plan.tables) - set(dataset_policy.tables))
    if unexpected_tables:
        raise PolicyViolation(f"Query plan uses disallowed tables: {', '.join(unexpected_tables)}")

    unexpected_fields = sorted(set(query_plan.fields) - set(dataset_policy.allowed_fields))
    if unexpected_fields:
        raise PolicyViolation(f"Query plan returns disallowed fields: {', '.join(unexpected_fields)}")

    if int(query_plan.params.get("max_rows", 0)) > profile.max_rows:
        raise PolicyViolation("Query plan row limit exceeds the permission profile limit.")

    sql = query_plan.sql.strip()
    if not sql.lower().startswith("select"):
        raise PolicyViolation("Only SELECT queries are allowed.")
    if ";" in sql:
        raise PolicyViolation("Semicolons are not allowed in generated SQL.")
    if FORBIDDEN_SQL_RE.search(sql):
        raise PolicyViolation("Generated SQL contains a forbidden statement.")

    referenced_tables = set(TABLE_REF_RE.findall(sql))
    unexpected_sql_tables = sorted(referenced_tables - set(dataset_policy.tables))
    if unexpected_sql_tables:
        raise PolicyViolation(
            f"SQL references disallowed tables: {', '.join(unexpected_sql_tables)}"
        )

    if not profile.allow_raw_sql and not query_plan.template_id:
        raise PolicyViolation("Raw SQL is disabled for this permission profile.")


def resolve_output_dir(
    output_dir: str | Path | None,
    profile: PermissionProfile,
) -> Path:
    configured_root = Path(profile.output_root).expanduser()
    selected_output = Path(output_dir).expanduser() if output_dir else configured_root

    root_resolved = configured_root.resolve(strict=False)
    selected_resolved = selected_output.resolve(strict=False)
    try:
        selected_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PolicyViolation(
            f"Output directory {selected_output} is outside allowed root {configured_root}."
        ) from exc

    return selected_output


def enforce_row_limit(row_count: int, profile: PermissionProfile) -> None:
    if row_count > profile.max_rows:
        raise PolicyViolation(
            f"Result has {row_count} rows; profile limit is {profile.max_rows} rows."
        )
