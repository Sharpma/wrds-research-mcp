from __future__ import annotations

from wrds_research_mcp.models import ResearchRequest, SecurityIdentifier


DEMO_SECURITIES = {
    "AAPL": SecurityIdentifier(
        ticker="AAPL",
        permno=14593,
        company_name="Apple Inc.",
        source="demo_static_map",
    )
}


def resolve_security_identifier(request: ResearchRequest) -> SecurityIdentifier:
    ticker = request.ticker.upper()
    try:
        return DEMO_SECURITIES[ticker]
    except KeyError as exc:
        raise ValueError(
            f"Ticker {ticker!r} is not in the demo identifier map. "
            "The demo currently supports AAPL."
        ) from exc
