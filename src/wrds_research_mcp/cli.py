from __future__ import annotations

import argparse
import json
import sys

from wrds_research_mcp.pipeline import run_research_request
from wrds_research_mcp.policy import PolicyViolation


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
        "--profile",
        default="demo",
        help="Permission profile from config/permissions.yaml.",
    )
    parser.add_argument(
        "--policy-path",
        default=None,
        help="Path to the MCP permission policy file.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for parquet and metadata outputs. Must be inside the profile output root.",
    )
    parser.add_argument(
        "--source",
        choices=["mock", "wrds"],
        default=None,
        help="Override data source. Must match the selected permission profile.",
    )
    args = parser.parse_args()

    try:
        result = run_research_request(
            args.request,
            output_dir=args.output_dir,
            source=args.source,
            profile=args.profile,
            policy_path=args.policy_path,
        )
    except PolicyViolation as exc:
        print(f"Permission denied: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
