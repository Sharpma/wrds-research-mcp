# Security Policy

`wrds-research-mcp` is designed to expose guarded WRDS access to local agents. Please treat
credentials and vendor data as sensitive.

## Supported Versions

The project is currently alpha. Security fixes target the latest commit on the active
development branch until the first stable release is tagged.

## Reporting a Vulnerability

Please report suspected security issues privately to the repository maintainers instead of
opening a public issue with exploit details.

Include:

- affected version or commit
- operating system and Python version
- a minimal reproduction
- whether WRDS credentials or data may have been exposed

## Credential Guidance

- Use `wrds-research-setup` to write PostgreSQL `pgpass`.
- Do not pass WRDS passwords through MCP config, chat, shell history, or README examples.
- Do not commit `.env`, `pgpass`, Parquet outputs, CSV exports, or vendor data samples.

## Data Access Model

The MCP server does not provide a raw SQL tool. Access is mediated through permission
profiles, approved query plans, live dictionary discovery, and structured generic filters.
