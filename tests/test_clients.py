import pytest

from wrds_research_mcp.clients import _wrds_connection_kwargs


def test_wrds_connection_kwargs_requires_username(monkeypatch) -> None:
    for key in ["WRDS_USERNAME", "WRDS_USER", "PGUSER", "WRDS_PASSWORD", "WRDS_PASS", "PGPASSWORD"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PGPASSFILE", "__missing_pgpass_for_test__")

    with pytest.raises(RuntimeError, match="username is not configured"):
        _wrds_connection_kwargs()


def test_wrds_connection_kwargs_reads_wrds_environment(monkeypatch) -> None:
    monkeypatch.setenv("WRDS_USERNAME", "sample_user")
    monkeypatch.setenv("WRDS_PASSWORD", "sample_password")

    assert _wrds_connection_kwargs() == {
        "wrds_username": "sample_user",
        "wrds_password": "sample_password",
    }


def test_wrds_connection_kwargs_reads_pgpass_username(monkeypatch, tmp_path) -> None:
    from wrds_research_mcp.credentials import setup_wrds_credentials

    for key in ["WRDS_USERNAME", "WRDS_USER", "PGUSER", "WRDS_PASSWORD", "WRDS_PASS", "PGPASSWORD"]:
        monkeypatch.delenv(key, raising=False)

    pgpass = tmp_path / "pgpass.conf"
    setup_wrds_credentials("pgpass_user", "pgpass_password", pgpass)
    monkeypatch.setenv("PGPASSFILE", str(pgpass))

    assert _wrds_connection_kwargs() == {"wrds_username": "pgpass_user"}
