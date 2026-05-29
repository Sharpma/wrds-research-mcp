from __future__ import annotations

import calendar
import re
from collections.abc import Iterable
from datetime import date

from wrds_research_mcp.models import ResearchRequest


COMPANY_ALIASES = {
    "苹果公司": ("Apple Inc.", "AAPL"),
    "苹果": ("Apple Inc.", "AAPL"),
    "apple": ("Apple Inc.", "AAPL"),
    "aapl": ("Apple Inc.", "AAPL"),
}


DAY_PATTERNS = [
    re.compile(r"(?P<year>19\d{2}|20\d{2})\s*年\s*(?P<month>0?[1-9]|1[0-2])\s*月\s*(?P<day>0?[1-9]|[12]\d|3[01])\s*日"),
    re.compile(r"(?P<year>19\d{2}|20\d{2})[-/](?P<month>0?[1-9]|1[0-2])[-/](?P<day>0?[1-9]|[12]\d|3[01])"),
]

MONTH_PATTERNS = [
    re.compile(r"(?P<year>19\d{2}|20\d{2})\s*年\s*(?P<month>0?[1-9]|1[0-2])\s*月"),
    re.compile(r"(?P<year>19\d{2}|20\d{2})[-/](?P<month>0?[1-9]|1[0-2])(?![-/]\d)"),
]

YEAR_PATTERNS = [
    re.compile(r"(?P<year>19\d{2}|20\d{2})\s*年"),
    re.compile(r"\b(?P<year>19\d{2}|20\d{2})\b"),
]


def parse_research_request(text: str) -> ResearchRequest:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Request text is empty.")

    company, ticker = _parse_company(clean_text)
    start_date, end_date = _parse_date_range(clean_text)

    fields = _parse_fields(clean_text)
    frequency = _parse_frequency(clean_text)
    dataset = "crsp_monthly_returns" if frequency == "monthly" else "crsp_daily_returns"

    return ResearchRequest(
        original_text=clean_text,
        dataset=dataset,
        company=company,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        fields=fields,
    )


def _parse_company(text: str) -> tuple[str, str]:
    lowered = text.lower()
    for alias, value in COMPANY_ALIASES.items():
        if alias in lowered or alias in text:
            return value

    ticker_match = re.search(r"\b[A-Z]{1,5}\b", text)
    if ticker_match:
        ticker = ticker_match.group(0)
        return ticker, ticker

    raise ValueError("Could not identify a company or ticker. Demo currently supports Apple/AAPL.")


def _parse_date_range(text: str) -> tuple[date, date]:
    day_matches: list[date] = []
    for pattern in DAY_PATTERNS:
        day_matches.extend(_dates_from_matches(pattern.finditer(text)))

    if len(day_matches) >= 2:
        start_date, end_date = day_matches[0], day_matches[1]
        if end_date < start_date:
            start_date, end_date = end_date, start_date
        return start_date, end_date

    if len(day_matches) == 1:
        return day_matches[0], day_matches[0]

    for pattern in MONTH_PATTERNS:
        match = pattern.search(text)
        if match:
            year = int(match.group("year"))
            month = int(match.group("month"))
            last_day = calendar.monthrange(year, month)[1]
            return date(year, month, 1), date(year, month, last_day)

    for pattern in YEAR_PATTERNS:
        match = pattern.search(text)
        if match:
            year = int(match.group("year"))
            return date(year, 1, 1), date(year, 12, 31)

    raise ValueError("Could not identify a date range. Try a month such as 2025年1月 or 2025-01.")


def _dates_from_matches(matches: Iterable[re.Match[str]]) -> list[date]:
    parsed = []
    for match in matches:
        parsed.append(
            date(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            )
        )
    return parsed


def _parse_fields(text: str) -> list[str]:
    lowered = text.lower()
    fields = []

    if "收益" in text or "return" in lowered or "ret" in lowered:
        fields.append("ret")
    if "价格" in text or "price" in lowered or "prc" in lowered:
        fields.append("prc")
    if "成交量" in text or "volume" in lowered or "vol" in lowered:
        fields.append("vol")

    return fields or ["ret"]


def _parse_frequency(text: str) -> str:
    lowered = text.lower()
    if "月度" in text or "monthly" in lowered or "month-end" in lowered:
        return "monthly"
    return "daily"
