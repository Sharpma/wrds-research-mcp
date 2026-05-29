# wrds-research-mcp

`wrds-research-mcp` is an MCP server and Python CLI for guarded WRDS research data access.
It lets an agent discover available WRDS libraries and tables, inspect table dictionaries,
choose an approved extraction path, and materialize analysis-ready Parquet files.

The project is currently alpha. It includes:

- a WRDS read-only profile for real WRDS access
- approved CRSP daily and monthly return workflows
- live WRDS library/table/column discovery
- guarded generic table extracts with structured filters
- Parquet outputs plus JSON metadata

The server intentionally does not expose a raw SQL execution tool.
Data extraction requires valid WRDS credentials.

## Install

Prerequisites on Windows:

```powershell
py --version
git --version
py -m pip install --user pipx
py -m pipx ensurepath
```

Restart PowerShell after `ensurepath`, then install:

```powershell
pipx install "wrds-research-mcp[all] @ git+https://github.com/Sharpma/wrds-research-mcp.git"
```

If `pipx` is still not on `PATH`, use:

```powershell
py -m pipx install "wrds-research-mcp[all] @ git+https://github.com/Sharpma/wrds-research-mcp.git"
```

For source development:

```powershell
git clone https://github.com/Sharpma/wrds-research-mcp.git
cd wrds-research-mcp
uv sync --python 3.11 --extra all --extra dev
```

## Configure WRDS

Run the setup helper once on each machine:

```powershell
wrds-research-setup
```

It prompts for your WRDS username and password, writes the standard PostgreSQL `pgpass`
file, and tests the connection. After setup, the MCP server can infer your username from
`pgpass`; you should not need to put credentials in command-line arguments, README files,
MCP config, or chat.

Run a real WRDS request:

```powershell
wrds-research `
  "Get AAPL monthly returns for 2025"
```

The default `wrds_readonly` profile writes outputs under `~/.wrds-research-mcp/data/wrds`.

## Use With Codex

For local development, register the stdio MCP server:

```powershell
codex mcp add wrds-research-mcp -- wrds-research-mcp
```

If PowerShell blocks `codex.ps1` with an execution policy error, use the Windows command
shim instead:

```powershell
codex.cmd mcp add wrds-research-mcp -- wrds-research-mcp
```

Alternatively, allow locally installed scripts for the current user:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Do not add WRDS passwords through `codex mcp add --env`. Use `wrds-research-setup`
instead.

If Codex says the server is configured but the current session has no WRDS tools, remove
and re-add the entry to clear malformed command text, then start a new Codex session:

```powershell
codex.cmd mcp remove wrds-research-mcp
codex.cmd mcp add wrds-research-mcp -- wrds-research-mcp
codex.cmd mcp get --json wrds-research-mcp
```

The server is a stdio MCP process, so running `wrds-research-mcp` directly may appear to
hang. That is expected; it is waiting for MCP JSON-RPC messages on stdin.

For the shortest agent path, call the execution tool directly and omit `output_dir` unless
you have a custom policy:

```text
get_research_data(
  request="Get AAPL monthly returns for 2025"
)
```

This uses `wrds_readonly` by default and writes under `~/.wrds-research-mcp/data/wrds`.

## MCP Tools

The MCP server exposes discoverable tools and resources:

- `list_wrds_profiles`: list profiles, sources, limits, and allowlists
- `list_wrds_datasets`: list locally approved dataset contracts
- `describe_wrds_dataset`: inspect one approved dataset contract
- `read_wrds_data_dictionary`: read catalog or live WRDS table metadata
- `search_wrds_data_dictionary`: search catalog or live dictionary metadata
- `list_accessible_wrds_libraries`: list live WRDS libraries visible to the account
- `list_accessible_wrds_tables`: list live tables in one library
- `describe_accessible_wrds_table`: inspect live columns for one `library.table`
- `probe_accessible_wrds_tables`: check SELECT privilege without reading table rows
- `materialize_accessible_wrds_table`: write a guarded Parquet extract using structured filters
- `plan_wrds_research_request`: parse a natural-language request into an approved plan
- `get_research_data`: execute an approved CRSP returns workflow and write Parquet

Recommended agent flow:

```text
list_wrds_profiles
list_wrds_datasets(profile="wrds_readonly")
list_accessible_wrds_libraries(profile="wrds_readonly")
list_accessible_wrds_tables(profile="wrds_readonly", library="crsp", search="stkmth")
describe_accessible_wrds_table(profile="wrds_readonly", library="crsp", table="stkmthsecuritydata")
plan_wrds_research_request(request="Get AAPL monthly returns for 2025", profile="wrds_readonly")
get_research_data(request="Get AAPL monthly returns for 2025", profile="wrds_readonly")
```

Generic extracts use structured arguments, not raw SQL:

```text
materialize_accessible_wrds_table(
  profile="wrds_readonly",
  library="crsp",
  table="stkmthsecuritydata",
  columns=["permno", "ticker", "mthcaldt", "mthret"],
  filters=[
    {"column": "permno", "op": "eq", "value": 14593},
    {"column": "mthcaldt", "op": "between", "start": "2025-01-01", "end": "2025-12-31"}
  ],
  limit=1000
)
```

Resources:

```text
wrds://profiles
wrds://datasets
wrds://dictionary
```

## Permission Model

Default policy is packaged with the library in `wrds_research_mcp/default_permissions.yaml`.
A repo copy is also kept at `config/permissions.yaml` as an editable template.

Profiles control:

- source backend: `wrds`
- approved dataset contracts
- maximum date span
- maximum rows
- maximum generic extract rows
- allowed output root
- allowed and blocked WRDS libraries
- raw SQL access, disabled by default

Use a custom policy file with:

```powershell
wrds-research "Get AAPL daily returns for 2025-01" --policy-path config/permissions.yaml
```

## Development

```powershell
uv sync --python 3.11 --extra all --extra dev
uv run pytest
uv build
```

Generated Parquet files and credentials are ignored by git.

## Project Status

This package is not affiliated with WRDS, Wharton, CRSP, Compustat, or any data vendor.
Users are responsible for complying with their WRDS subscription and vendor data licenses.

Current high-level limits:

- natural-language parsing is intentionally narrow
- static identifier resolution currently covers AAPL only
- approved canned workflows currently cover CRSP daily and monthly stock returns
- broader WRDS coverage is available through live discovery plus guarded generic extracts
