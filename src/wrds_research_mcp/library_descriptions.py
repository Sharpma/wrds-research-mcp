from __future__ import annotations

from fnmatch import fnmatchcase
from typing import Any


GUIDANCE_SOURCE = "built_in_llm_guidance"

LIBRARY_GUIDANCE_RULES: list[dict[str, Any]] = [
    {
        "patterns": ["crsp", "crsp_*", "crspa", "crspm"],
        "title": "CRSP",
        "description": "Security prices, returns, shares, distributions, delistings, indexes, and identifiers for US equity and market research.",
        "topics": ["stock returns", "prices", "permno", "permco", "delistings", "indexes"],
        "agent_hint": "Use for US stock returns, prices, trading volume, delisting-adjusted returns, CRSP identifiers, and market index data.",
    },
    {
        "patterns": ["comp", "comp_*", "compdcur", "compg", "compm", "compsamp*"],
        "title": "Compustat",
        "description": "Company fundamentals, accounting statements, segment data, security metadata, and global firm financials.",
        "topics": ["fundamentals", "financial statements", "gvkey", "accounting", "segments"],
        "agent_hint": "Use for balance sheet, income statement, cash flow, accounting ratios, fiscal periods, and GVKEY-based firm data.",
    },
    {
        "patterns": ["ibes", "ibes_*", "ibesg", "ibescorp"],
        "title": "IBES",
        "description": "Analyst forecasts, recommendations, earnings estimates, actuals, and analyst-level forecast history.",
        "topics": ["analyst forecasts", "earnings estimates", "recommendations", "eps", "actuals"],
        "agent_hint": "Use for consensus forecasts, analyst recommendations, forecast revisions, and earnings surprise studies.",
    },
    {
        "patterns": ["optionm", "optionm_*", "optionmsamp*"],
        "title": "OptionMetrics",
        "description": "US equity option prices, implied volatility surfaces, option identifiers, and security-option link data.",
        "topics": ["options", "implied volatility", "option prices", "volatility surface"],
        "agent_hint": "Use for option contracts, implied volatility, Greeks, volatility surface data, and option-equity matching.",
    },
    {
        "patterns": ["taq", "taq_*", "taqmsec", "taqmsamp*"],
        "title": "TAQ",
        "description": "Intraday trades and quotes data for market microstructure, liquidity, spreads, and high-frequency studies.",
        "topics": ["intraday", "trades", "quotes", "spreads", "market microstructure"],
        "agent_hint": "Use for trade-and-quote data, bid-ask spreads, intraday volume, liquidity, and microstructure research.",
    },
    {
        "patterns": ["audit*", "auditanalytics*"],
        "title": "Audit Analytics",
        "description": "Audit, auditor, restatement, internal-control, fee, and regulatory disclosure datasets.",
        "topics": ["audit", "restatements", "internal controls", "auditor", "fees"],
        "agent_hint": "Use for audit opinions, auditor changes, restatements, SOX/internal control issues, and audit fees.",
    },
    {
        "patterns": ["boardex*"],
        "title": "BoardEx",
        "description": "Board directors, executives, employment history, compensation roles, education, and network relationships.",
        "topics": ["directors", "executives", "boards", "networks", "biographies"],
        "agent_hint": "Use for director/executive characteristics, board composition, interlocks, and management networks.",
    },
    {
        "patterns": ["execcomp*"],
        "title": "ExecuComp",
        "description": "Executive compensation, named executive officer details, pay components, and governance-related identifiers.",
        "topics": ["executive compensation", "ceo", "options", "salary", "governance"],
        "agent_hint": "Use for CEO/CFO pay, incentives, option grants, total compensation, and executive identifiers.",
    },
    {
        "patterns": ["iss*", "riskmetrics*"],
        "title": "ISS / RiskMetrics",
        "description": "Corporate governance, board structure, voting, shareholder proposals, and governance ratings data.",
        "topics": ["governance", "proxy voting", "shareholder proposals", "directors"],
        "agent_hint": "Use for governance attributes, director elections, voting outcomes, and shareholder proposal research.",
    },
    {
        "patterns": ["csmar*"],
        "title": "CSMAR",
        "description": "China-focused market, accounting, corporate governance, ownership, analyst, and transaction datasets.",
        "topics": ["china", "a-shares", "accounting", "ownership", "governance"],
        "agent_hint": "Use for Chinese listed companies, A-share returns, financial statements, ownership, governance, and China-specific events.",
    },
    {
        "patterns": ["tr", "tr_*", "refinitiv*", "thomson*"],
        "title": "Refinitiv / Thomson Reuters",
        "description": "Refinitiv/Thomson data families, often including ownership, deals, estimates, events, or security reference data depending on subscription.",
        "topics": ["ownership", "deals", "events", "reference data", "thomson reuters"],
        "agent_hint": "Inspect tables first. Use when the request mentions Thomson, Refinitiv, institutional holdings, deals, or event datasets.",
    },
    {
        "patterns": ["tfn*", "13f*", "tr_13f*"],
        "title": "Thomson 13F / Institutional Holdings",
        "description": "Institutional ownership and 13F holdings data for investors, managers, securities, and quarterly holdings.",
        "topics": ["13f", "institutional ownership", "holdings", "managers"],
        "agent_hint": "Use for institutional holdings, manager ownership, 13F filings, and investor-level equity positions.",
    },
    {
        "patterns": ["fisd*"],
        "title": "Mergent FISD",
        "description": "Fixed income securities, bond issue details, coupons, ratings, covenants, and issuer-level bond metadata.",
        "topics": ["bonds", "fixed income", "ratings", "coupons", "covenants"],
        "agent_hint": "Use for corporate bonds, bond characteristics, ratings, issue data, coupons, and maturity structure.",
    },
    {
        "patterns": ["trace*", "msrb*"],
        "title": "Bond Trade Data",
        "description": "Corporate or municipal bond transactions, trade reports, prices, volumes, and dealer-market activity.",
        "topics": ["bond trades", "fixed income", "municipal bonds", "transaction prices"],
        "agent_hint": "Use for bond transaction prices, trade volume, liquidity, and corporate or municipal bond market studies.",
    },
    {
        "patterns": ["ff", "ff_*", "ff_all"],
        "title": "Fama-French / Factor Data",
        "description": "Research factors, portfolios, benchmark returns, and asset-pricing factor datasets.",
        "topics": ["asset pricing", "factors", "portfolios", "benchmark returns"],
        "agent_hint": "Use for Fama-French factors, portfolio returns, factor models, and benchmark asset-pricing series.",
    },
    {
        "patterns": ["zacks*", "zacksamp*"],
        "title": "Zacks",
        "description": "Earnings estimates, actuals, surprises, recommendations, and company forecast-related datasets.",
        "topics": ["earnings estimates", "surprises", "recommendations", "analyst data"],
        "agent_hint": "Use for Zacks earnings forecasts, recommendations, actuals, surprises, and estimate revisions.",
    },
    {
        "patterns": ["factset*", "fds*"],
        "title": "FactSet",
        "description": "FactSet data families, often including fundamentals, estimates, ownership, supply chain, entity, and security reference data.",
        "topics": ["factset", "ownership", "fundamentals", "estimates", "supply chain"],
        "agent_hint": "Inspect tables first. Use when the request references FactSet, entity mapping, ownership, estimates, or supply-chain data.",
    },
    {
        "patterns": ["ciq*", "capitaliq*", "ciqsamp*"],
        "title": "Capital IQ",
        "description": "S&P Capital IQ data families, often including company fundamentals, identifiers, transactions, key developments, people, and security reference data.",
        "topics": ["capital iq", "company fundamentals", "key developments", "transactions", "identifiers"],
        "agent_hint": "Inspect tables first. Use when the request references Capital IQ, key developments, company screening, entity identifiers, or transaction/event data.",
    },
    {
        "patterns": ["bvd*", "bvdsamp*", "orbis*"],
        "title": "Bureau van Dijk / Orbis",
        "description": "Global private and public company information, ownership, financials, corporate groups, and entity reference datasets.",
        "topics": ["private firms", "ownership", "orbis", "global companies", "entity data"],
        "agent_hint": "Use for private-company financials, global entity matching, ownership structures, subsidiaries, and corporate group data.",
    },
    {
        "patterns": ["ravenpack*", "rpna*"],
        "title": "RavenPack",
        "description": "News analytics, event sentiment, entity-event tagging, relevance, novelty, and media-derived event data.",
        "topics": ["news", "sentiment", "events", "media analytics"],
        "agent_hint": "Use for news sentiment, event detection, entity-level media signals, and textual-news event studies.",
    },
    {
        "patterns": ["reprisk*"],
        "title": "RepRisk",
        "description": "ESG controversy, business conduct risk, environmental, social, governance, and reputational risk data.",
        "topics": ["esg", "controversies", "reputation risk", "sustainability"],
        "agent_hint": "Use for ESG incident risk, controversies, reputational risk, and sustainability-related event studies.",
    },
    {
        "patterns": ["sustainalytics*", "msci_esg*", "kld*"],
        "title": "ESG Ratings",
        "description": "Environmental, social, governance ratings, controversy indicators, and sustainability-related firm measures.",
        "topics": ["esg", "ratings", "controversies", "sustainability"],
        "agent_hint": "Use for ESG scores, sustainability metrics, controversies, and responsible-investing research.",
    },
    {
        "patterns": ["pitchbook*", "venturexpert*", "sdc*"],
        "title": "Deals / Private Markets",
        "description": "Private equity, venture capital, mergers, acquisitions, financing rounds, and deal transaction datasets.",
        "topics": ["m&a", "venture capital", "private equity", "deals"],
        "agent_hint": "Use for M&A transactions, VC/PE rounds, deal participants, transaction values, and private-market activity.",
    },
    {
        "patterns": ["calcbench*"],
        "title": "Calcbench",
        "description": "XBRL-based SEC filing data, standardized financial statement tags, footnotes, and filing-derived metrics.",
        "topics": ["xbrl", "sec filings", "financial statements", "footnotes"],
        "agent_hint": "Use for tagged filing data, XBRL financial statements, footnote text, and SEC filing analytics.",
    },
    {
        "patterns": ["aha*", "ahasamp*"],
        "title": "AHA Annual Survey",
        "description": "American Hospital Association healthcare organization data, hospital characteristics, services, ownership, beds, and facility-level attributes.",
        "topics": ["healthcare", "hospitals", "facilities", "services", "ownership"],
        "agent_hint": "Use for hospital characteristics, healthcare facility attributes, hospital services, ownership type, and healthcare market structure.",
    },
    {
        "patterns": ["cboe*", "phlx*", "otc*"],
        "title": "Exchange / Options Market Data",
        "description": "Exchange-specific market datasets such as option markets, OTC activity, quotes, trades, or security reference data depending on subscription.",
        "topics": ["exchange data", "options", "quotes", "trades", "otc"],
        "agent_hint": "Inspect tables first. Use for exchange-specific options, quotes, trades, OTC securities, and market activity datasets.",
    },
    {
        "patterns": ["frb*", "macrofin*", "pwt*", "totalq*", "doe*"],
        "title": "Macroeconomic / Government Data",
        "description": "Macroeconomic, government, energy, international accounts, or aggregate financial datasets depending on the library.",
        "topics": ["macroeconomics", "government", "energy", "aggregate data", "international"],
        "agent_hint": "Use for macro variables, aggregate financial indicators, government or energy datasets, and international macro comparisons.",
    },
    {
        "patterns": ["iri*", "dmef*", "infogroup*", "candid*"],
        "title": "Marketing / Organization Data",
        "description": "Marketing, consumer, organization, nonprofit, or business-location datasets depending on subscription and table family.",
        "topics": ["marketing", "consumer", "organizations", "locations", "nonprofits"],
        "agent_hint": "Inspect tables first. Use for consumer panels, marketing data, business listings, nonprofit organizations, or location-based organization data.",
    },
    {
        "patterns": ["ftse*", "ftsesamp*", "msci*"],
        "title": "Index / Classification Data",
        "description": "Index constituents, classifications, benchmarks, ESG/index reference data, or market classification datasets depending on subscription.",
        "topics": ["indexes", "classifications", "benchmarks", "constituents", "msci"],
        "agent_hint": "Use for index membership, benchmark constituents, market classifications, and index-related reference data.",
    },
    {
        "patterns": ["bank*", "snl*"],
        "title": "Banking / SNL Financial",
        "description": "Bank, financial institution, regulatory, branch, holding-company, and industry financial datasets.",
        "topics": ["banks", "financial institutions", "regulatory", "branches"],
        "agent_hint": "Use for banks, financial institutions, regulatory filings, branch data, and industry-specific financials.",
    },
    {
        "patterns": ["mfl*", "hfr*", "barclayhedge*"],
        "title": "Funds / Hedge Funds",
        "description": "Mutual fund, hedge fund, fund returns, holdings, flows, fees, and fund characteristics datasets.",
        "topics": ["mutual funds", "hedge funds", "fund returns", "holdings", "flows"],
        "agent_hint": "Use for fund returns, holdings, flows, fees, fund characteristics, and fund-performance studies.",
    },
    {
        "patterns": ["etfg*"],
        "title": "ETF Global",
        "description": "ETF characteristics, holdings, classifications, flows, and exchange-traded fund reference data.",
        "topics": ["etf", "holdings", "flows", "fund characteristics"],
        "agent_hint": "Use for ETF holdings, fund flows, ETF classifications, expenses, and ETF-level analytics.",
    },
    {
        "patterns": ["markit*", "cds*"],
        "title": "Markit / Credit Market Data",
        "description": "Credit market datasets such as CDS, loan, index, pricing, or reference data depending on subscription.",
        "topics": ["credit", "cds", "loans", "pricing", "indexes"],
        "agent_hint": "Inspect tables first. Use for CDS, credit indices, loan pricing, and credit-market research.",
    },
    {
        "patterns": ["twoiq*", "insider*"],
        "title": "Insider Transactions",
        "description": "Insider trades, directors' dealings, ownership transactions, and officer/director transaction data.",
        "topics": ["insider trading", "directors", "ownership transactions"],
        "agent_hint": "Use for insider purchases/sales, director dealings, executive ownership transactions, and trade timing studies.",
    },
    {
        "patterns": ["djones*", "dj_*", "dowjones*"],
        "title": "Dow Jones",
        "description": "Dow Jones news, entities, events, and media-derived datasets depending on subscription.",
        "topics": ["news", "events", "dow jones", "media"],
        "agent_hint": "Inspect tables first. Use when the request references Dow Jones news, media events, or entity news coverage.",
    },
]


def describe_library(library: str, detailed: bool = False) -> dict[str, Any]:
    normalized = library.lower()
    for rule in LIBRARY_GUIDANCE_RULES:
        if any(fnmatchcase(normalized, pattern) for pattern in rule["patterns"]):
            return _guidance_entry(library, rule, "medium", detailed)

    fallback = {
        "title": _humanize_library_name(library),
        "description": (
            f"Visible WRDS library `{library}`. No built-in domain description is available; "
            "inspect its tables and columns before selecting it for extraction."
        ),
        "topics": _tokens_from_library_name(library),
        "agent_hint": (
            "Use list_accessible_wrds_tables and describe_accessible_wrds_table to inspect "
            "available tables, date fields, identifiers, and join keys before extracting data."
        ),
    }
    return _guidance_entry(library, fallback, "low", detailed)


def library_search_text(entry: dict[str, Any]) -> str:
    values = [
        entry.get("library"),
        entry.get("title"),
        entry.get("description"),
        entry.get("agent_hint"),
        " ".join(entry.get("topics", [])),
    ]
    if "detail" in entry:
        values.append(entry["detail"].get("selection_caution"))
    return " ".join(str(value or "") for value in values).lower()


def _guidance_entry(
    library: str,
    rule: dict[str, Any],
    confidence: str,
    detailed: bool,
) -> dict[str, Any]:
    entry = {
        "library": library,
        "title": rule["title"],
        "description": rule["description"],
        "topics": rule["topics"],
        "agent_hint": rule["agent_hint"],
        "guidance_source": GUIDANCE_SOURCE,
        "guidance_confidence": confidence,
    }
    if detailed:
        entry["detail"] = {
            "selection_caution": (
                "This description is orientation guidance, not an authoritative WRDS data "
                "dictionary. Always inspect live tables and columns before extraction."
            ),
            "recommended_next_tools": [
                "list_accessible_wrds_tables",
                "describe_accessible_wrds_table",
                "materialize_accessible_wrds_table",
            ],
        }
    return entry


def _humanize_library_name(library: str) -> str:
    return " ".join(part.upper() if len(part) <= 4 else part.title() for part in library.split("_"))


def _tokens_from_library_name(library: str) -> list[str]:
    return [part for part in library.lower().replace("-", "_").split("_") if part]
