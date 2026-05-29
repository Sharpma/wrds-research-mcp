from wrds_research_mcp.discovery import _library_allowed_for_report
from wrds_research_mcp.policy import get_permission_profile, load_policy_document


def test_discovery_filters_blocked_libraries() -> None:
    document = load_policy_document()
    profile = get_permission_profile(document, "wrds_readonly")

    assert _library_allowed_for_report("crsp", profile)
    assert not _library_allowed_for_report("pg_catalog", profile)
