from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wrds_research_mcp.discovery import describe_wrds_table
from wrds_research_mcp.policy import (
    get_permission_profile,
    load_policy_document,
    resolve_output_dir,
    validate_generic_limit,
    validate_library_access,
    validate_table_identifier,
)
from wrds_research_mcp.wrds_connection import connect_wrds_quietly


SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ALLOWED_FILTER_OPS = {"eq", "ne", "gt", "gte", "lt", "lte", "between", "in", "like"}


def materialize_wrds_table(
    library: str,
    table: str,
    columns: list[str] | None = None,
    filters: list[dict[str, Any]] | None = None,
    limit: int = 1000,
    profile: str = "wrds_readonly",
    output_dir: str | Path | None = None,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(document, profile)
    if permission_profile.source != "wrds":
        raise ValueError(f"Profile {profile!r} is not backed by WRDS.")

    validate_library_access(library, permission_profile)
    validate_table_identifier(table)
    validate_generic_limit(limit, permission_profile)
    output_root = resolve_output_dir(output_dir, permission_profile)

    table_description = describe_wrds_table(
        library=library,
        table=table,
        profile=profile,
        policy_path=policy_path,
    )
    available_columns = [
        column["name"]
        for column in table_description["columns"]
        if column.get("name")
    ]
    selected_columns = _select_columns(columns, available_columns)
    where_sql, params = _build_filter_sql(filters or [], available_columns)
    params["limit"] = limit

    sql = _build_select_sql(library, table, selected_columns, where_sql)
    db = connect_wrds_quietly()
    dataframe = db.raw_sql(sql, params=params)

    materialized = _write_generic_dataframe(
        dataframe=dataframe,
        output_root=output_root,
        library=library,
        table=table,
        profile=profile,
        sql=sql,
        params=params,
        selected_columns=selected_columns,
        filters=filters or [],
    )
    return materialized


def _select_columns(columns: list[str] | None, available_columns: list[str]) -> list[str]:
    if not columns:
        return available_columns

    available = set(available_columns)
    selected = []
    for column in columns:
        _validate_column_name(column)
        if column not in available:
            raise ValueError(f"Column {column!r} is not present in the selected table.")
        selected.append(column)
    return selected


def _build_filter_sql(
    filters: list[dict[str, Any]],
    available_columns: list[str],
) -> tuple[str, dict[str, Any]]:
    available = set(available_columns)
    clauses = []
    params: dict[str, Any] = {}

    for index, filter_spec in enumerate(filters):
        column = str(filter_spec.get("column", ""))
        op = str(filter_spec.get("op", "eq")).lower()
        _validate_column_name(column)
        if column not in available:
            raise ValueError(f"Filter column {column!r} is not present in the selected table.")
        if op not in ALLOWED_FILTER_OPS:
            raise ValueError(f"Unsupported filter op {op!r}.")

        identifier = _quote_identifier(column)
        param_name = f"f{index}"

        if op == "between":
            start = filter_spec.get("start")
            end = filter_spec.get("end")
            if start is None or end is None:
                value = filter_spec.get("value")
                if not isinstance(value, list | tuple) or len(value) != 2:
                    raise ValueError("between filters require start/end or a two-item value list.")
                start, end = value
            params[f"{param_name}_start"] = start
            params[f"{param_name}_end"] = end
            clauses.append(
                f"{identifier} between %({param_name}_start)s and %({param_name}_end)s"
            )
        elif op == "in":
            values = filter_spec.get("values", filter_spec.get("value"))
            if not isinstance(values, list | tuple) or not values:
                raise ValueError("in filters require a non-empty values list.")
            names = []
            for value_index, value in enumerate(values):
                value_name = f"{param_name}_{value_index}"
                params[value_name] = value
                names.append(f"%({value_name})s")
            clauses.append(f"{identifier} in ({', '.join(names)})")
        else:
            if "value" not in filter_spec:
                raise ValueError(f"{op} filters require value.")
            params[param_name] = filter_spec["value"]
            operator = {
                "eq": "=",
                "ne": "!=",
                "gt": ">",
                "gte": ">=",
                "lt": "<",
                "lte": "<=",
                "like": "like",
            }[op]
            clauses.append(f"{identifier} {operator} %({param_name})s")

    if not clauses:
        return "", params
    return "where " + " and ".join(clauses), params


def _build_select_sql(
    library: str,
    table: str,
    selected_columns: list[str],
    where_sql: str,
) -> str:
    column_sql = ", ".join(_quote_identifier(column) for column in selected_columns)
    return f"""
select {column_sql}
from {_quote_identifier(library)}.{_quote_identifier(table)}
{where_sql}
limit %(limit)s
""".strip()


def _write_generic_dataframe(
    dataframe,
    output_root: Path,
    library: str,
    table: str,
    profile: str,
    sql: str,
    params: dict[str, Any],
    selected_columns: list[str],
    filters: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install parquet support with: pip install wrds-research-mcp") from exc

    generated_at = datetime.now(timezone.utc)
    table_dir = output_root / "generic" / f"library-{library}" / f"table-{table}"
    table_dir.mkdir(parents=True, exist_ok=True)
    stem = generated_at.strftime("%Y%m%dT%H%M%SZ")
    parquet_path = table_dir / f"{stem}.parquet"
    metadata_path = table_dir / f"{stem}.metadata.json"

    arrow_table = pa.Table.from_pandas(dataframe, preserve_index=False)
    pq.write_table(arrow_table, parquet_path)

    metadata = {
        "generated_at": generated_at.isoformat(),
        "profile": profile,
        "source": "wrds",
        "library": library,
        "table": table,
        "selected_columns": selected_columns,
        "filters": filters,
        "row_count": int(len(dataframe)),
        "query": {
            "sql": sql,
            "params": params,
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "output_path": str(parquet_path),
        "metadata_path": str(metadata_path),
        "row_count": int(len(dataframe)),
        "library": library,
        "table": table,
        "columns": list(dataframe.columns),
    }


def _validate_column_name(column: str) -> None:
    if not SAFE_IDENTIFIER_RE.fullmatch(column):
        raise ValueError(f"Unsafe column name: {column!r}")


def _quote_identifier(identifier: str) -> str:
    if not SAFE_IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"Unsafe identifier: {identifier!r}")
    return f'"{identifier}"'
