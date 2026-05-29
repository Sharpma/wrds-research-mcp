from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
from typing import Any

from wrds_research_mcp.catalog import CATALOG
from wrds_research_mcp.clients import _wrds_connection_kwargs
from wrds_research_mcp.policy import get_dataset_policy, get_permission_profile, load_policy_document


def read_data_dictionary(
    profile: str = "wrds_readonly",
    dataset: str | None = None,
    source: str = "catalog",
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(document, profile)
    dataset_names = _allowed_dataset_names(permission_profile.allowed_datasets, dataset)
    normalized_source = source.lower()

    if normalized_source == "catalog":
        datasets = {
            dataset_name: _catalog_dataset_dictionary(document, dataset_name)
            for dataset_name in dataset_names
        }
    elif normalized_source == "wrds":
        if permission_profile.source != "wrds":
            raise ValueError(f"Profile {profile!r} is not backed by WRDS.")
        datasets = _wrds_dataset_dictionaries(document, dataset_names)
    else:
        raise ValueError("source must be either 'catalog' or 'wrds'.")

    return {
        "profile": profile,
        "source": normalized_source,
        "scope": "profile_allowlist",
        "datasets": datasets,
    }


def search_data_dictionary(
    query: str,
    profile: str = "wrds_readonly",
    dataset: str | None = None,
    source: str = "catalog",
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    needle = query.strip().lower()
    if not needle:
        raise ValueError("query must not be empty.")

    dictionary = read_data_dictionary(
        profile=profile,
        dataset=dataset,
        source=source,
        policy_path=policy_path,
    )
    matches = []
    for dataset_name, dataset_entry in dictionary["datasets"].items():
        if _matches(needle, dataset_name, dataset_entry.get("description", "")):
            matches.append(
                {
                    "kind": "dataset",
                    "dataset": dataset_name,
                    "label": dataset_entry.get("label"),
                    "description": dataset_entry.get("description"),
                }
            )

        for table_name, table_entry in dataset_entry.get("tables", {}).items():
            if _matches(needle, table_name, table_entry.get("description", "")):
                matches.append(
                    {
                        "kind": "table",
                        "dataset": dataset_name,
                        "table": table_name,
                        "description": table_entry.get("description"),
                    }
                )

            for column in table_entry.get("columns", []):
                if _matches(needle, column.get("name", ""), column.get("comment", "")):
                    matches.append(
                        {
                            "kind": "column",
                            "dataset": dataset_name,
                            "table": table_name,
                            "column": column,
                        }
                    )

    return {
        "profile": dictionary["profile"],
        "source": dictionary["source"],
        "query": query,
        "matches": matches,
    }


def _catalog_dataset_dictionary(document: dict[str, Any], dataset_name: str) -> dict[str, Any]:
    dataset_policy = get_dataset_policy(document, dataset_name)
    catalog_entry = CATALOG.get(dataset_name, {})
    logical_columns = [
        {
            "name": field_name,
            "type": "logical",
            "nullable": None,
            "comment": comment,
        }
        for field_name, comment in catalog_entry.get("fields", {}).items()
    ]

    tables = {
        table_name: {
            "description": "Approved source table. Use source='wrds' for live WRDS column metadata.",
            "columns": logical_columns,
        }
        for table_name in dataset_policy.tables
    }
    return {
        "label": catalog_entry.get("label", dataset_name),
        "description": dataset_policy.description,
        "frequency": catalog_entry.get("frequency"),
        "identifiers": catalog_entry.get("identifiers", []),
        "required_filters": dataset_policy.required_filters,
        "allowed_query_templates": dataset_policy.allowed_query_templates,
        "tables": tables,
    }


def _wrds_dataset_dictionaries(
    document: dict[str, Any],
    dataset_names: list[str],
) -> dict[str, Any]:
    try:
        import wrds
    except ImportError as exc:
        raise RuntimeError("Install WRDS support with: uv sync --extra wrds") from exc

    with redirect_stdout(io.StringIO()):
        db = wrds.Connection(**_wrds_connection_kwargs())
    datasets = {}
    for dataset_name in dataset_names:
        dataset_policy = get_dataset_policy(document, dataset_name)
        catalog_entry = CATALOG.get(dataset_name, {})
        tables = {}
        for table_ref in dataset_policy.tables:
            library, table = _split_table_ref(table_ref)
            description = f"Live WRDS metadata for {table_ref}."
            columns = _describe_wrds_table(db, library, table)
            tables[table_ref] = {
                "description": description,
                "columns": columns,
            }

        datasets[dataset_name] = {
            "label": catalog_entry.get("label", dataset_name),
            "description": dataset_policy.description,
            "frequency": catalog_entry.get("frequency"),
            "identifiers": catalog_entry.get("identifiers", []),
            "required_filters": dataset_policy.required_filters,
            "allowed_query_templates": dataset_policy.allowed_query_templates,
            "tables": tables,
        }
    return datasets


def _describe_wrds_table(db: Any, library: str, table: str) -> list[dict[str, Any]]:
    with redirect_stdout(io.StringIO()):
        dataframe = db.describe_table(library=library, table=table)
    columns = []
    for row in dataframe.to_dict("records"):
        columns.append(
            {
                "name": _none_if_missing(row.get("name")),
                "type": _string_or_none(row.get("type")),
                "nullable": _none_if_missing(row.get("nullable")),
                "comment": _none_if_missing(row.get("comment")),
            }
        )
    return columns


def _allowed_dataset_names(allowed_datasets: list[str], dataset: str | None) -> list[str]:
    if dataset is None:
        return allowed_datasets
    if dataset not in allowed_datasets:
        raise ValueError(f"Dataset {dataset!r} is not allowed by the selected profile.")
    return [dataset]


def _split_table_ref(table_ref: str) -> tuple[str, str]:
    try:
        library, table = table_ref.split(".", 1)
    except ValueError as exc:
        raise ValueError(f"Table reference must be schema.table: {table_ref}") from exc
    return library, table


def _matches(needle: str, *values: str | None) -> bool:
    return any(needle in str(value or "").lower() for value in values)


def _none_if_missing(value: Any) -> Any:
    try:
        if value != value:
            return None
    except TypeError:
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            return value
    return value


def _string_or_none(value: Any) -> str | None:
    normalized = _none_if_missing(value)
    if normalized is None:
        return None
    return str(normalized)
