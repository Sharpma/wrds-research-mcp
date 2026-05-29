import json

import pytest

from wrds_research_mcp.pipeline import run_research_request


def test_pipeline_materializes_mock_parquet(tmp_path) -> None:
    parquet = pytest.importorskip("pyarrow.parquet")
    policy_path = _write_test_policy(tmp_path)

    result = run_research_request(
        "Get AAPL daily return data for 2025-01",
        profile="test_demo",
        policy_path=policy_path,
    )

    assert result.dataset.row_count > 0
    assert result.dataset.output_path.exists()
    assert result.dataset.output_path.suffix == ".parquet"
    assert result.dataset.metadata_path.exists()
    assert result.permission_profile == "test_demo"

    table = parquet.read_table(result.dataset.output_path)
    assert table.num_rows == result.dataset.row_count
    assert "ticker" in table.column_names

    metadata = json.loads(result.dataset.metadata_path.read_text(encoding="utf-8"))
    assert metadata["request"]["ticker"] == "AAPL"
    assert metadata["source"] == "mock"
    assert metadata["permission_profile"] == "test_demo"
    assert "crsp.stkdlysecuritydata" in metadata["catalog"]["tables"]


def _write_test_policy(tmp_path):
    output_root = (tmp_path / "outputs").as_posix()
    policy_path = tmp_path / "permissions.yaml"
    policy_path.write_text(
        f"""
profiles:
  test_demo:
    source: mock
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
