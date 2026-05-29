import pytest

from wrds_research_mcp.clients import _wrds_connection_kwargs


def test_wrds_connection_kwargs_requires_username(monkeypatch) -> None:
    for key in ["WRDS_USERNAME", "WRDS_USER", "PGUSER", "WRDS_PASSWORD", "WRDS_PASS", "PGPASSWORD"]:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError, match="username is not configured"):
        _wrds_connection_kwargs()


def test_wrds_connection_kwargs_reads_wrds_environment(monkeypatch) -> None:
    monkeypatch.setenv("WRDS_USERNAME", "demo_user")
    monkeypatch.setenv("WRDS_PASSWORD", "demo_password")

    assert _wrds_connection_kwargs() == {
        "wrds_username": "demo_user",
        "wrds_password": "demo_password",
    }
