import json
from datetime import date

import pytest

from wrds_research_mcp.pipeline import run_research_request


def test_pipeline_materializes_wrds_result_with_injected_client(tmp_path, monkeypatch) -> None:
    parquet = pytest.importorskip("pyarrow.parquet")
    policy_path = _write_test_policy(tmp_path)
    monkeypatch.setattr(
        "wrds_research_mcp.pipeline.get_data_client",
        lambda source: _FakeWRDSClient(source),
    )

    result = run_research_request(
        "Get AAPL daily return data for 2025-01",
        profile="test_wrds",
        policy_path=policy_path,
    )

    assert result.dataset.row_count == 1
    assert result.dataset.output_path.exists()
    assert result.dataset.output_path.suffix == ".parquet"
    assert result.dataset.metadata_path.exists()
    assert result.permission_profile == "test_wrds"
    assert result.source == "wrds"

    table = parquet.read_table(result.dataset.output_path)
    assert table.num_rows == result.dataset.row_count
    assert "ticker" in table.column_names

    metadata = json.loads(result.dataset.metadata_path.read_text(encoding="utf-8"))
    assert metadata["request"]["ticker"] == "AAPL"
    assert metadata["source"] == "wrds"
    assert metadata["permission_profile"] == "test_wrds"
    assert "crsp.stkdlysecuritydata" in metadata["catalog"]["tables"]


class _FakeWRDSClient:
    def __init__(self, source: str) -> None:
        assert source == "wrds"

    def fetch_returns(self, request, security, query_plan):
        return [
            {
                "date": date(2025, 1, 2),
                "permno": security.permno,
                "ticker": security.ticker,
                "company_name": security.company_name,
                "ret": 0.01,
                "retx": 0.01,
                "prc": 243.85,
                "vol": 55_700_000,
                "source": "wrds",
            }
        ]


def _write_test_policy(tmp_path):
    output_root = (tmp_path / "outputs").as_posix()
    policy_path = tmp_path / "permissions.yaml"
    policy_path.write_text(
        f"""
profiles:
  test_wrds:
    source: wrds
    allowed_datasets:
      - crsp_daily_returns
    max_date_span_days: 366
    max_rows: 100000
    output_root: {output_root}
    allow_raw_sql: false

datasets:
  crsp_daily_returns:
    tables:
      - crsp.stkdlysecuritydata
      - crsp.stocknames_v2
    allowed_fields:
      - date
      - permno
      - ticker
      - company_name
      - ret
      - retx
      - prc
      - vol
      - source
    required_filters:
      - date_range
      - security_identifier
    allowed_frequencies:
      - daily
    allowed_output_formats:
      - parquet
    allowed_query_templates:
      - crsp_daily_returns_v2
""",
        encoding="utf-8",
    )
    return policy_path
