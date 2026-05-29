import json

import pytest

from wrds_research_mcp.pipeline import run_research_request


def test_pipeline_materializes_mock_parquet(tmp_path) -> None:
    parquet = pytest.importorskip("pyarrow.parquet")

    result = run_research_request(
        "我现在要2025年1月苹果公司的日度收益率数据",
        output_dir=tmp_path,
        source="mock",
    )

    assert result.dataset.row_count > 0
    assert result.dataset.output_path.exists()
    assert result.dataset.output_path.suffix == ".parquet"
    assert result.dataset.metadata_path.exists()

    table = parquet.read_table(result.dataset.output_path)
    assert table.num_rows == result.dataset.row_count
    assert "ticker" in table.column_names

    metadata = json.loads(result.dataset.metadata_path.read_text(encoding="utf-8"))
    assert metadata["request"]["ticker"] == "AAPL"
    assert metadata["source"] == "mock"
    assert "crsp.dsf" in metadata["catalog"]["tables"]
