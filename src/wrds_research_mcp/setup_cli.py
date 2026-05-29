from __future__ import annotations

import argparse
import json
import sys

from wrds_research_mcp.credentials import (
    setup_wrds_credentials,
    test_wrds_credentials,
    prompt_and_setup_wrds_credentials,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure WRDS credentials for wrds-research-mcp.",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="WRDS username. If omitted, the command prompts for it.",
    )
    parser.add_argument(
        "--pgpass-path",
        default=None,
        help="Override pgpass file path. Usually not needed.",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Write credentials without testing the WRDS connection.",
    )
    parser.add_argument(
        "--password-stdin",
        action="store_true",
        help="Read the WRDS password from stdin. Intended for scripts; interactive prompt is preferred.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable setup status.",
    )
    args = parser.parse_args()

    try:
        if args.password_stdin:
            username = (args.username or input("WRDS username: ")).strip()
            password = sys.stdin.readline().rstrip("\r\n")
            target = setup_wrds_credentials(username, password, args.pgpass_path)
            connection_test = {"attempted": False, "ok": None, "message": "skipped"}
            if not args.skip_test:
                connection_test = test_wrds_credentials(username)
            result = {
                "pgpass_path": str(target),
                "username": username,
                "connection_test": connection_test,
            }
        else:
            result = prompt_and_setup_wrds_credentials(
                username=args.username,
                path=args.pgpass_path,
                test_connection=not args.skip_test,
            )
    except (RuntimeError, ValueError) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"WRDS credentials saved to: {result['pgpass_path']}")
    connection_test = result["connection_test"]
    if connection_test["attempted"]:
        if connection_test["ok"]:
            print("WRDS connection test succeeded.")
        else:
            print(f"WRDS connection test failed: {connection_test['message']}", file=sys.stderr)
            raise SystemExit(2)
    else:
        print("WRDS connection test skipped.")


if __name__ == "__main__":
    main()
