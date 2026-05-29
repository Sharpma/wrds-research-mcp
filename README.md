# wrds-research-mcp

Natural-language access layer for WRDS research data.

This `demo` branch contains a minimal, runnable proof of concept:

1. Parse a natural-language request such as `我现在要2025年1月苹果公司的日度收益率数据`.
2. Convert it into a structured CRSP daily returns request.
3. Resolve Apple/AAPL to a demo CRSP identifier.
4. Build a parameterized WRDS SQL query plan for `crsp.dsf` and `crsp.stocknames`.
5. Validate the request against `config/permissions.yaml`.
6. Materialize deterministic mock rows as Parquet plus metadata.

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

## Permission Policy

MCP data access is controlled by `config/permissions.yaml`.

The demo intentionally avoids exposing a raw SQL tool. The model can submit a research request, but the server only executes approved query templates against approved datasets.

Current profiles:

- `demo`: uses deterministic mock data and writes under `data/demo`
- `wrds_readonly`: uses WRDS and writes under `data/wrds`

Each profile controls:

- allowed datasets
- source backend, such as `mock` or `wrds`
- maximum date span
- maximum returned rows
- allowed output root
- whether raw SQL is allowed

Run a specific profile:

```powershell
uv run wrds-research-demo "Get AAPL daily returns for 2025-01" --profile demo
```

The server rejects requests that try to use a source, table, field, query template, or output directory outside the selected profile.

## Optional WRDS Mode

Install optional WRDS support:

```powershell
uv sync --extra wrds
```

Then run:

```powershell
uv run wrds-research-demo "Get AAPL daily returns for 2025-01" --profile wrds_readonly
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
get_research_data(
  request: str,
  profile: str = "demo",
  output_dir: str | None = None,
  source: str | None = None,
  policy_path: str | None = None
)
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
