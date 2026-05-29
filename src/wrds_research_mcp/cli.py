from __future__ import annotations

import argparse
import json

from wrds_research_mcp.pipeline import run_research_request


DEFAULT_REQUEST = "我现在要2025年1月苹果公司的日度收益率数据"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the minimal WRDS research data demo.",
    )
    parser.add_argument(
        "request",
        nargs="?",
        default=DEFAULT_REQUEST,
        help="Natural-language research data request.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/demo",
        help="Directory for parquet and metadata outputs.",
    )
    parser.add_argument(
        "--source",
        choices=["mock", "wrds"],
        default="mock",
        help="Use deterministic mock data or query WRDS.",
    )
    args = parser.parse_args()

    result = run_research_request(args.request, output_dir=args.output_dir, source=args.source)
    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
