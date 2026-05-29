from __future__ import annotations

from wrds_research_mcp.models import ResearchRequest, SecurityIdentifier


AAPL_SECURITY = {
    "AAPL": SecurityIdentifier(
        ticker="AAPL",
        permno=14593,
        company_name="Apple Inc.",
        source="static_identifier_map",
    )
}


def resolve_security_identifier(request: ResearchRequest) -> SecurityIdentifier:
    ticker = request.ticker.upper()
    try:
        return AAPL_SECURITY[ticker]
    except KeyError as exc:
        raise ValueError(
            f"Ticker {ticker!r} is not in the static identifier map. "
            "The current approved workflow supports AAPL until identifier lookup is expanded."
        ) from exc
