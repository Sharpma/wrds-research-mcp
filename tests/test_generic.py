import pytest

from wrds_research_mcp.generic import _build_filter_sql, _build_select_sql, _select_columns
from wrds_research_mcp.policy import (
    PolicyViolation,
    get_permission_profile,
    load_policy_document,
    validate_generic_limit,
    validate_library_access,
)


def test_select_columns_rejects_unknown_column() -> None:
    with pytest.raises(ValueError, match="not present"):
        _select_columns(["missing"], ["permno", "date"])


def test_build_filter_sql_uses_parameters() -> None:
    sql, params = _build_filter_sql(
        [
            {"column": "permno", "op": "eq", "value": 14593},
            {"column": "date", "op": "between", "start": "2025-01-01", "end": "2025-01-31"},
        ],
        ["permno", "date"],
    )

    assert '"permno" = %(f0)s' in sql
    assert '"date" between %(f1_start)s and %(f1_end)s' in sql
    assert params["f0"] == 14593


def test_build_select_sql_quotes_identifiers() -> None:
    sql = _build_select_sql("crsp", "stkmthsecuritydata", ["permno", "mthret"], "")

    assert 'from "crsp"."stkmthsecuritydata"' in sql
    assert 'select "permno", "mthret"' in sql


def test_generic_policy_allows_wrds_libraries_and_blocks_system_schemas() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "wrds_readonly")

    validate_library_access("crsp", profile)
    with pytest.raises(PolicyViolation, match="blocked"):
        validate_library_access("pg_catalog", profile)


def test_generic_policy_enforces_limit() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "wrds_readonly")

    validate_generic_limit(profile.max_generic_rows, profile)
    with pytest.raises(PolicyViolation, match="exceeds"):
        validate_generic_limit(profile.max_generic_rows + 1, profile)
