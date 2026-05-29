# wrds-research-mcp

Natural-language access layer for WRDS research data.

This `demo` branch contains a minimal, runnable proof of concept:

1. Parse a natural-language request such as `我现在要2025年1月苹果公司的日度收益率数据`.
2. Convert it into a structured CRSP daily or monthly returns request.
3. Resolve Apple/AAPL to a demo CRSP identifier.
4. Build a parameterized WRDS SQL query plan from an approved query template.
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

## New Machine Setup

On a fresh machine, use the setup helper once. It prompts for your WRDS username and password, writes the standard PostgreSQL `pgpass` file, and tests the WRDS connection.

```powershell
git clone https://github.com/Sharpma/wrds-research-mcp.git
cd wrds-research-mcp
git switch demo
uv run --python 3.11 --extra wrds wrds-research-setup
```

After that, WRDS commands and the MCP server can discover the username from `pgpass`; you should not need to set `$env:WRDS_USERNAME` manually.

Interactive setup is the recommended path. `wrds-research-setup --password-stdin` exists for automation when a secret manager can pipe the password securely.

Test with real WRDS:

```powershell
uv run --python 3.11 --extra wrds wrds-research-demo "Get AAPL monthly returns for 2025" --profile wrds_readonly
```

Register with Codex:

```powershell
codex mcp add wrds-research-mcp -- uv --directory <path-to-wrds-research-mcp> run --python 3.11 --extra mcp --extra wrds wrds-research-mcp
```

Do not put WRDS passwords in `codex mcp add --env`, `.env`, README examples, or chat.

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
uv run wrds-research-demo "Get AAPL monthly returns for 2025" --profile demo
```

The server rejects requests that try to use a source, table, field, query template, or output directory outside the selected profile.

## Optional WRDS Mode

Install optional WRDS support:

```powershell
uv sync --python 3.11 --extra wrds
```

The WRDS package path is tested with Python 3.11/3.12. The project avoids Python 3.13+ for now because the WRDS dependency stack may not provide compatible wheels there yet.

Configure credentials locally. Do not paste WRDS passwords into Codex chat.

```powershell
uv run --python 3.11 --extra wrds wrds-research-setup
```

Alternatively, set `WRDS_USERNAME`/`WRDS_PASSWORD` yourself, but the setup helper is the preferred path.

Then run:

```powershell
uv run --python 3.11 --extra wrds wrds-research-demo "Get AAPL daily returns for 2025-01" --profile wrds_readonly
uv run --python 3.11 --extra wrds wrds-research-demo "Get AAPL monthly returns for 2025" --profile wrds_readonly
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

The MCP server exposes discoverable tools instead of a raw SQL endpoint:

- `list_wrds_profiles`: discover profiles, sources, limits, and dataset allowlists
- `list_wrds_datasets`: discover datasets allowed by a profile
- `describe_wrds_dataset`: inspect identifiers, fields, tables, templates, and limits
- `read_wrds_data_dictionary`: read allowed dataset/table/field metadata
- `search_wrds_data_dictionary`: search the allowed data dictionary
- `plan_wrds_research_request`: parse natural language into an approved request and query plan
- `get_research_data`: execute the approved request and write Parquet plus metadata

Recommended Agent flow:

```text
list_wrds_profiles
list_wrds_datasets(profile="wrds_readonly")
read_wrds_data_dictionary(profile="wrds_readonly", source="catalog")
describe_wrds_dataset(dataset="crsp_monthly_returns", profile="wrds_readonly")
search_wrds_data_dictionary(query="monthly return", dataset="crsp_monthly_returns")
plan_wrds_research_request(request="Get AAPL monthly returns for 2025", profile="wrds_readonly")
get_research_data(request="Get AAPL monthly returns for 2025", profile="wrds_readonly")
```

`read_wrds_data_dictionary` supports two sources:

- `catalog`: local policy/catalog metadata, no WRDS connection required
- `wrds`: live WRDS table descriptions for approved tables only

The execution tool accepts:

```text
get_research_data(
  request: str,
  profile: str = "demo",
  output_dir: str | None = None,
  source: str | None = None,
  policy_path: str | None = None
)
```

The server also exposes JSON resources:

```text
wrds://profiles
wrds://datasets
wrds://dictionary
```

## Tests

```powershell
uv run --extra dev pytest
```

## Current Demo Limits

- Only Apple/AAPL is included in the static identifier map.
- Natural-language parsing is intentionally rule-based and narrow.
- Current deterministic query templates cover CRSP daily and monthly stock returns.
- Mock data is deterministic and is not real WRDS/CRSP data.
- Real WRDS mode requires valid WRDS access and the optional `wrds` package.
