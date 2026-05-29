# Contributing

Thanks for helping improve `wrds-research-mcp`.

## Development Setup

```powershell
git clone https://github.com/Sharpma/wrds-research-mcp.git
cd wrds-research-mcp
uv sync --python 3.11 --extra all --extra dev
uv run pytest
```

WRDS credentials are optional for most unit tests. Unit tests should inject test-only
fakes or monkeypatch WRDS clients instead of adding user-facing local data paths.

## Pull Request Guidelines

- Keep data access behind named tools or approved query plans.
- Do not add raw SQL execution tools.
- Do not commit credentials, generated data, or vendor data samples.
- Add focused tests for policy, parsing, query construction, and output metadata changes.
- Update README examples when command names or MCP tools change.

## Live WRDS Testing

For changes that need real WRDS access:

```powershell
uv run --python 3.11 --extra wrds wrds-research-setup
uv run --python 3.11 --extra wrds wrds-research "Get AAPL monthly returns for 2025"
```

Do not paste WRDS passwords into issues, pull requests, logs, or chat transcripts.
