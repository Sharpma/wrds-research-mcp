from datetime import date

import pytest

from wrds_research_mcp.models import QueryPlan, ResearchRequest
from wrds_research_mcp.policy import (
    PolicyViolation,
    get_dataset_policy,
    get_permission_profile,
    load_policy_document,
    resolve_output_dir,
    validate_query_policy,
    validate_request_policy,
    validate_source,
)


def test_demo_profile_rejects_wrds_source() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "demo")

    with pytest.raises(PolicyViolation, match="not allowed"):
        validate_source("wrds", profile)


def test_policy_rejects_too_wide_date_range() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "demo")
    dataset_policy = get_dataset_policy(document, "crsp_daily_returns")
    request = ResearchRequest(
        original_text="Get AAPL returns",
        dataset="crsp_daily_returns",
        company="Apple Inc.",
        ticker="AAPL",
        start_date=date(2024, 1, 1),
        end_date=date(2025, 12, 31),
        frequency="daily",
        fields=["ret"],
    )

    with pytest.raises(PolicyViolation, match="profile limit"):
        validate_request_policy(request, profile, dataset_policy)


def test_policy_rejects_output_dir_outside_profile_root() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "demo")

    with pytest.raises(PolicyViolation, match="outside allowed root"):
        resolve_output_dir("data/not-demo", profile)


def test_policy_rejects_disallowed_query_table() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "demo")
    dataset_policy = get_dataset_policy(document, "crsp_daily_returns")
    query_plan = QueryPlan(
        sql="select * from comp.funda",
        params={"max_rows": 100},
        dataset="crsp_daily_returns",
        tables=["comp.funda"],
        fields=["ret"],
        template_id="crsp_daily_returns_v2",
    )

    with pytest.raises(PolicyViolation, match="disallowed tables"):
        validate_query_policy(query_plan, profile, dataset_policy)
