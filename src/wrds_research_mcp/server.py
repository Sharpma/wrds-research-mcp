from __future__ import annotations

from wrds_research_mcp.pipeline import run_research_request


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install MCP support with: uv sync --extra mcp") from exc

    mcp = FastMCP("wrds-research-mcp")

    @mcp.tool()
    def get_research_data(
        request: str,
        profile: str = "demo",
        output_dir: str | None = None,
        source: str | None = None,
        policy_path: str | None = None,
    ) -> dict:
        """Parse a research request, fetch CRSP daily returns, and write parquet."""
        return run_research_request(
            request,
            output_dir=output_dir,
            source=source,
            profile=profile,
            policy_path=policy_path,
        ).as_dict()

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
