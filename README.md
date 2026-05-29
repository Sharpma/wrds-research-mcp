# wrds-research-mcp

Natural-language access layer for WRDS research data.

This `demo` branch contains a minimal, runnable proof of concept:

1. Parse a natural-language request such as `我现在要2025年1月苹果公司的日度收益率数据`.
2. Convert it into a structured CRSP daily returns request.
3. Resolve Apple/AAPL to a demo CRSP identifier.
4. Build a parameterized WRDS SQL query plan for `crsp.dsf` and `crsp.stocknames`.
5. Materialize deterministic mock rows as Parquet plus metadata.

The default path uses mock data so the demo can run before WRDS credentials are configured. A WRDS client hook is included for the same query plan.

## Quick Start

```powershell
git switch demo
uv run wrds-research-demo
```

Run with an explicit request:

```powershell
uv run wrds-research-demo "我现在要2025年1月苹果公司的日度收益率数据"
```

The demo writes ignored local outputs under:

```text
data/demo/crsp_daily_returns/symbol=AAPL/
```

Each run produces:

- `*.parquet`: analysis-ready tabular data
- `*.metadata.json`: request, identifier, catalog, and SQL query plan metadata

## Optional WRDS Mode

Install optional WRDS support:

```powershell
uv sync --extra wrds
```

Then run:

```powershell
uv run wrds-research-demo "Get AAPL daily returns for 2025-01" --source wrds
```

WRDS authentication should be configured through the normal WRDS mechanisms, such as `.pgpass` or environment-backed local configuration. Do not commit credentials.

## Optional MCP Server

Install optional MCP support:

```powershell
uv sync --extra mcp
```

Run the stdio MCP server:

```powershell
uv run wrds-research-mcp
```

The demo server exposes one tool:

```text
get_research_data(request: str, output_dir: str = "data/demo", source: str = "mock")
```

## Tests

```powershell
uv run --extra dev pytest
```

## Current Demo Limits

- Only Apple/AAPL is included in the static identifier map.
- Natural-language parsing is intentionally rule-based and narrow.
- Mock data is deterministic and is not real WRDS/CRSP data.
- Real WRDS mode requires valid WRDS access and the optional `wrds` package.
