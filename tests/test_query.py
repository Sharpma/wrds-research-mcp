from datetime import date

from wrds_research_mcp.models import ResearchRequest, SecurityIdentifier
from wrds_research_mcp.query import build_crsp_daily_returns_query, build_crsp_monthly_returns_query


def test_crsp_daily_returns_uses_current_daily_security_table() -> None:
    request = ResearchRequest(
        original_text="Get AAPL daily returns for 2025-01",
        dataset="crsp_daily_returns",
        company="Apple Inc.",
        ticker="AAPL",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        frequency="daily",
        fields=["ret"],
    )
    security = SecurityIdentifier(
        ticker="AAPL",
        permno=14593,
        company_name="Apple Inc.",
        source="test",
    )

    query_plan = build_crsp_daily_returns_query(request, security, max_rows=100)

    assert "crsp.stkdlysecuritydata" in query_plan.sql
    assert "crsp.stocknames_v2" in query_plan.sql
    assert "d.dlycaldt as date" in query_plan.sql
    assert "d.dlyret::double precision as ret" in query_plan.sql
    assert query_plan.template_id == "crsp_daily_returns_v2"


def test_crsp_monthly_returns_uses_current_monthly_security_table() -> None:
    request = ResearchRequest(
        original_text="Get AAPL monthly returns for 2025",
        dataset="crsp_monthly_returns",
        company="Apple Inc.",
        ticker="AAPL",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        frequency="monthly",
        fields=["ret"],
    )
    security = SecurityIdentifier(
        ticker="AAPL",
        permno=14593,
        company_name="Apple Inc.",
        source="test",
    )

    query_plan = build_crsp_monthly_returns_query(request, security, max_rows=100)

    assert "crsp.stkmthsecuritydata" in query_plan.sql
    assert "d.mthcaldt as date" in query_plan.sql
    assert "d.mthret::double precision as ret" in query_plan.sql
    assert query_plan.template_id == "crsp_monthly_returns_v1"
