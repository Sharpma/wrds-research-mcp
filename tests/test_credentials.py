from wrds_research_mcp.credentials import (
    find_wrds_username_in_pgpass,
    setup_wrds_credentials,
    wrds_pgpass_exists,
)


def test_setup_wrds_credentials_writes_pgpass_and_finds_username(tmp_path) -> None:
    pgpass = tmp_path / "pgpass.conf"

    setup_wrds_credentials("sample_user", "sample_password", pgpass)

    assert pgpass.exists()
    assert find_wrds_username_in_pgpass(pgpass) == "sample_user"
    assert wrds_pgpass_exists(pgpass)


def test_setup_wrds_credentials_replaces_existing_wrds_entry(tmp_path) -> None:
    pgpass = tmp_path / "pgpass.conf"

    setup_wrds_credentials("old_user", "old_password", pgpass)
    setup_wrds_credentials("new_user", "new_password", pgpass)

    text = pgpass.read_text(encoding="utf-8")
    assert "old_user" not in text
    assert "new_user" in text
    assert find_wrds_username_in_pgpass(pgpass) == "new_user"


def test_setup_wrds_credentials_escapes_pgpass_colons(tmp_path) -> None:
    pgpass = tmp_path / "pgpass.conf"

    setup_wrds_credentials("sample:user", "pass:word", pgpass)

    text = pgpass.read_text(encoding="utf-8")
    assert "sample\\:user" in text
    assert "pass\\:word" in text
    assert find_wrds_username_in_pgpass(pgpass) == "sample:user"
