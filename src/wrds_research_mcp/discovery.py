from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
from typing import Any

from wrds_research_mcp.library_descriptions import describe_library, library_search_text
from wrds_research_mcp.policy import (
    get_permission_profile,
    load_policy_document,
    validate_library_access,
    validate_table_identifier,
)
from wrds_research_mcp.wrds_connection import is_transient_wrds_error, run_wrds_operation


def list_wrds_libraries(
    profile: str = "wrds_readonly",
    include_table_counts: bool = False,
    include_descriptions: bool = True,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    permission_profile = _wrds_profile(profile, policy_path)

    def read_libraries(db: Any) -> dict[str, Any]:
        libraries = []
        for library in sorted(db.list_libraries()):
            try:
                validate_library_access(library, permission_profile)
            except Exception:
                continue
            entry: dict[str, Any] = {"library": library}
            if include_descriptions:
                entry.update(describe_library(library, detailed=False))
            if include_table_counts:
                entry["table_count"] = len(db.list_tables(library=library))
            libraries.append(entry)

        return {
            "profile": profile,
            "catalog_scope": "live_wrds_libraries_visible_to_account",
            "guidance_note": (
                "Descriptions are orientation guidance. Inspect live tables and columns before extraction."
            ),
            "library_count": len(libraries),
            "libraries": libraries,
        }

    return run_wrds_operation(read_libraries)


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

    def read_tables(db: Any) -> dict[str, Any]:
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

    return run_wrds_operation(read_tables)


def describe_wrds_library(
    library: str,
    profile: str = "wrds_readonly",
    include_tables: bool = False,
    table_search: str | None = None,
    table_limit: int = 50,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    permission_profile = _wrds_profile(profile, policy_path)
    validate_library_access(library, permission_profile)
    guidance = describe_library(library, detailed=True)

    result = {
        "profile": profile,
        "catalog_scope": "single_live_wrds_library",
        "library": library,
        "guidance": guidance,
    }
    if include_tables:
        result["tables"] = list_wrds_tables(
            library=library,
            profile=profile,
            search=table_search,
            limit=table_limit,
            policy_path=policy_path,
        )
    return result


def search_wrds_libraries(
    query: str,
    profile: str = "wrds_readonly",
    limit: int = 25,
    policy_path: str | Path | None = None,
) -> dict[str, Any]:
    needle = query.strip().lower()
    if not needle:
        raise ValueError("query must not be empty.")
    if limit <= 0:
        raise ValueError("limit must be positive.")

    libraries = list_wrds_libraries(
        profile=profile,
        include_table_counts=False,
        include_descriptions=True,
        policy_path=policy_path,
    )["libraries"]
    matches = [
        library
        for library in libraries
        if all(term in library_search_text(library) for term in needle.split())
    ]
    return {
        "profile": profile,
        "query": query,
        "match_count": len(matches),
        "returned_count": min(len(matches), limit),
        "matches": matches[:limit],
        "next_step": "Use describe_accessible_wrds_library or list_accessible_wrds_tables on the best matching library.",
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

    def read_description(db: Any) -> dict[str, Any]:
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

    return run_wrds_operation(read_description)


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

    def read_access(db: Any) -> dict[str, Any]:
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

    return run_wrds_operation(read_access)


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
        if is_transient_wrds_error(exc):
            raise
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
