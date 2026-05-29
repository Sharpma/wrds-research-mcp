from datetime import date

from wrds_research_mcp.nlp import parse_research_request


def test_parse_chinese_daily_request() -> None:
    request = parse_research_request("我现在要2025年1月苹果公司的日度收益率数据")

    assert request.dataset == "crsp_daily_returns"
    assert request.company == "Apple Inc."
    assert request.ticker == "AAPL"
    assert request.start_date == date(2025, 1, 1)
    assert request.end_date == date(2025, 1, 31)
    assert request.frequency == "daily"
    assert request.fields == ["ret"]


def test_parse_english_ticker_request() -> None:
    request = parse_research_request("Get AAPL daily return data for 2025-01")

    assert request.ticker == "AAPL"
    assert request.start_date == date(2025, 1, 1)
    assert request.end_date == date(2025, 1, 31)


def test_parse_chinese_monthly_year_request() -> None:
    request = parse_research_request("我想获取苹果公司股票2025年的月度收益率数据")

    assert request.dataset == "crsp_monthly_returns"
    assert request.ticker == "AAPL"
    assert request.start_date == date(2025, 1, 1)
    assert request.end_date == date(2025, 12, 31)
    assert request.frequency == "monthly"
