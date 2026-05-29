from __future__ import annotations

import os

from wrds_research_mcp.credentials import wrds_pgpass_exists


DEMO_PROFILE = "demo"
WRDS_PROFILE = "wrds_readonly"
AUTO_PROFILE = "auto"


def resolve_profile_name(profile: str, source: str | None = None) -> str:
    if profile != AUTO_PROFILE:
        return profile

    if source == "wrds":
        return WRDS_PROFILE
    if source == "mock":
        return DEMO_PROFILE
    if wrds_credentials_look_configured():
        return WRDS_PROFILE
    return DEMO_PROFILE


def wrds_credentials_look_configured() -> bool:
    if _has_wrds_username_env() and _has_wrds_password_env():
        return True
    return wrds_pgpass_exists()


def _has_wrds_username_env() -> bool:
    return any(os.environ.get(name) for name in ("WRDS_USERNAME", "WRDS_USER", "PGUSER"))


def _has_wrds_password_env() -> bool:
    return any(os.environ.get(name) for name in ("WRDS_PASSWORD", "WRDS_PASS", "PGPASSWORD"))
