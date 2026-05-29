from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
from typing import Any

from wrds_research_mcp.policy import (
    get_permission_profile,
    load_policy_document,
    validate_library_access,
    validate_table_identifier,
)
from wrds_research_mcp.wrds_connection import connect_wrds_quietly


def list_wrds_libraries(
    profile: str = "wrds_readonly",
    include_table_counts: bool = False,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    permission_profile = _wrds_profile(profile, policy_path)
    db = connect_wrds_quietly()
    libraries = []
    for library in sorted(db.list_libraries()):
        try:
            validate_library_access(library, permission_profile)
        except Exception:
            continue
        entry: dict[str, Any] = {"library": library}
        if include_table_counts:
            entry["table_count"] = len(db.list_tables(library=library))
        libraries.append(entry)

    return {
        "profile": profile,
        "library_count": len(libraries),
        "libraries": libraries,
    }


def list_wrds_tables(
    library: str,
    profile: str = "wrds_readonly",
    search: str | None = None,
    limit: int = 500,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    permission_profile = _wrds_profile(profile, policy_path)
    validate_library_access(library, permission_profile)
    if limit <= 0:
        raise ValueError("limit must be positive.")

    db = connect_wrds_quietly()
    tables = sorted(db.list_tables(library=library))
    if search:
        needle = search.lower()
        tables = [table for table in tables if needle in table.lower()]

    return {
        "profile": profile,
        "library": library,
        "table_count": len(tables),
        "returned_count": min(len(tables), limit),
        "tables": tables[:limit],
    }


def describe_wrds_table(
    library: str,
    table: str,
    profile: str = "wrds_readonly",
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    permission_profile = _wrds_profile(profile, policy_path)
    validate_library_access(library, permission_profile)
    validate_table_identifier(table)

    db = connect_wrds_quietly()
    with redirect_stdout(io.StringIO()):
        description = db.describe_table(library=library, table=table)
    return {
        "profile": profile,
        "library": library,
        "table": table,
        "columns": [
            {
                "name": _none_if_missing(row.get("name")),
                "type": _string_or_none(row.get("type")),
                "nullable": _none_if_missing(row.get("nullable")),
                "comment": _none_if_missing(row.get("comment")),
            }
            for row in description.to_dict("records")
        ],
    }


def probe_wrds_table_access(
    profile: str = "wrds_readonly",
    library: str | None = None,
    search: str | None = None,
    limit: int = 5000,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    permission_profile = _wrds_profile(profile, policy_path)
    if library:
        validate_library_access(library, permission_profile)
    if limit <= 0:
        raise ValueError("limit must be positive.")

    db = connect_wrds_quietly()
    if library:
        rows, errors = _probe_one_library(db, library, limit, search)
    else:
        rows = []
        errors = []
        for candidate_library in sorted(db.list_libraries()):
            if not _library_allowed_for_report(candidate_library, permission_profile):
                continue
            if len(rows) >= limit:
                break
            remaining = limit - len(rows)
            library_rows, library_errors = _probe_one_library(
                db,
                candidate_library,
                remaining,
                search,
            )
            rows.extend(library_rows)
            errors.extend(library_errors)

    return {
        "profile": profile,
        "scope": library or "all_allowed_libraries",
        "returned_count": len(rows),
        "all_returned_selectable": all(bool(row["selectable"]) for row in rows),
        "errors": errors,
        "tables": rows,
    }


def _probe_one_library(
    db: Any,
    library: str,
    limit: int,
    search: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    params: dict[str, Any] = {"limit": limit}
    where = [
        "table_schema = %(library)s",
        "table_type in ('BASE TABLE', 'VIEW', 'FOREIGN TABLE')",
    ]
    params["library"] = library
    if search:
        where.append("(lower(table_schema) like %(search)s or lower(table_name) like %(search)s)")
        params["search"] = f"%{search.lower()}%"

    sql = f"""
select
    table_schema as library,
    table_name as table,
    table_type,
    has_table_privilege(
        format('%%I.%%I', table_schema, table_name),
        'SELECT'
    ) as selectable
from information_schema.tables
where {' and '.join(where)}
order by table_schema, table_name
limit %(limit)s
""".strip()
    try:
        dataframe = db.raw_sql(sql, params=params)
    except Exception as exc:
        return [], [{"library": library, "error": f"{type(exc).__name__}: {exc}"}]
    return dataframe.to_dict("records"), []


def _wrds_profile(profile: str, policy_path: str | Path | None):
    document = load_policy_document(policy_path)
    permission_profile = get_permission_profile(document, profile)
    if permission_profile.source != "wrds":
        raise ValueError(f"Profile {profile!r} is not backed by WRDS.")
    return permission_profile


def _library_allowed_for_report(library: str, permission_profile) -> bool:
    try:
        validate_library_access(library, permission_profile)
    except Exception:
        return False
    return True


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
