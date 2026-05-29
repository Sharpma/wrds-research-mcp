from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from wrds_research_mcp.catalog import CATALOG
from wrds_research_mcp.models import MaterializedDataset, QueryPlan, ResearchRequest, SecurityIdentifier


def write_parquet_dataset(
    rows: list[dict],
    output_dir: str | Path,
    request: ResearchRequest,
    security: SecurityIdentifier,
    query_plan: QueryPlan,
    source: str,
    permission_profile: str,
) -> MaterializedDataset:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install parquet support with: pip install wrds-research-mcp") from exc

    output_root = Path(output_dir)
    dataset_dir = output_root / request.dataset / f"symbol={security.ticker}"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    stem = f"{request.start_date.isoformat()}_{request.end_date.isoformat()}"
    parquet_path = dataset_dir / f"{stem}.parquet"
    metadata_path = dataset_dir / f"{stem}.metadata.json"

    schema = pa.schema(
        [
            ("date", pa.date32()),
            ("permno", pa.int64()),
            ("ticker", pa.string()),
            ("company_name", pa.string()),
            ("ret", pa.float64()),
            ("retx", pa.float64()),
            ("prc", pa.float64()),
            ("vol", pa.int64()),
            ("source", pa.string()),
        ]
    )
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(table, parquet_path)

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "permission_profile": permission_profile,
        "request": request.as_dict(),
        "security": security.as_dict(),
        "catalog": CATALOG[request.dataset],
        "query_plan": query_plan.as_dict(),
        "row_count": len(rows),
        "notes": [
            "Demo source returns deterministic mock rows.",
            "WRDS source uses the approved query plan against current CRSP security tables.",
            "Return fields are decimals, not percentages.",
        ],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return MaterializedDataset(
        output_path=parquet_path,
        metadata_path=metadata_path,
        row_count=len(rows),
    )
