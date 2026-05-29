from __future__ import annotations

import json

from wrds_research_mcp.capabilities import (
    get_dataset_contract,
    list_datasets,
    list_permission_profiles,
    plan_research_request,
)
from wrds_research_mcp.dictionary import read_data_dictionary, search_data_dictionary
from wrds_research_mcp.discovery import (
    describe_wrds_table,
    list_wrds_libraries,
    list_wrds_tables,
    probe_wrds_table_access,
)
from wrds_research_mcp.generic import materialize_wrds_table
from wrds_research_mcp.pipeline import run_research_request


def build_server():
    try:
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise RuntimeError(
            "Install MCP support with: pip install 'wrds-research-mcp[mcp]' "
            "or uv sync --extra mcp"
        ) from exc

    mcp = FastMCP("wrds-research-mcp")

    @mcp.resource(
        "wrds://profiles",
        name="WRDS permission profiles",
        description="Configured MCP profiles, data sources, dataset allowlists, and limits.",
        mime_type="application/json",
    )
    def profiles_resource() -> str:
        return json.dumps(list_permission_profiles(), ensure_ascii=False, indent=2)

    @mcp.resource(
        "wrds://datasets",
        name="WRDS dataset catalog",
        description="Datasets available to the default WRDS read-only profile.",
        mime_type="application/json",
    )
    def datasets_resource() -> str:
        return json.dumps(list_datasets(profile="wrds_readonly"), ensure_ascii=False, indent=2)

    @mcp.resource(
        "wrds://dictionary",
        name="WRDS data dictionary",
        description="Local catalog-backed dictionary for datasets allowed by the WRDS read-only profile.",
        mime_type="application/json",
    )
    def dictionary_resource() -> str:
        return json.dumps(
            read_data_dictionary(profile="wrds_readonly", source="catalog"),
            ensure_ascii=False,
            indent=2,
        )

    @mcp.tool(
        title="List WRDS permission profiles",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def list_wrds_profiles(policy_path: str | None = None) -> dict:
        """List MCP permission profiles, data sources, limits, and allowed datasets."""
        return list_permission_profiles(policy_path=policy_path)

    @mcp.tool(
        title="List WRDS datasets",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def list_wrds_datasets(
        profile: str = "wrds_readonly",
        policy_path: str | None = None,
    ) -> dict:
        """List datasets allowed by a profile, including frequencies and query templates."""
        return list_datasets(profile=profile, policy_path=policy_path)

    @mcp.tool(
        title="Describe WRDS dataset contract",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def describe_wrds_dataset(
        dataset: str,
        profile: str = "wrds_readonly",
        policy_path: str | None = None,
    ) -> dict:
        """Describe one dataset contract: identifiers, fields, tables, limits, and output rules."""
        return get_dataset_contract(dataset=dataset, profile=profile, policy_path=policy_path)

    @mcp.tool(
        title="Read WRDS data dictionary",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def read_wrds_data_dictionary(
        profile: str = "wrds_readonly",
        dataset: str | None = None,
        source: str = "catalog",
        policy_path: str | None = None,
    ) -> dict:
        """Read approved dataset/table/field metadata. Use source='wrds' for live WRDS descriptions."""
        return read_data_dictionary(
            profile=profile,
            dataset=dataset,
            source=source,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="Search WRDS data dictionary",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def search_wrds_data_dictionary(
        query: str,
        profile: str = "wrds_readonly",
        dataset: str | None = None,
        source: str = "catalog",
        policy_path: str | None = None,
    ) -> dict:
        """Search approved dictionary metadata by dataset, table, column name, or column comment."""
        return search_data_dictionary(
            query=query,
            profile=profile,
            dataset=dataset,
            source=source,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="List accessible WRDS libraries",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def list_accessible_wrds_libraries(
        profile: str = "wrds_readonly",
        include_table_counts: bool = False,
        policy_path: str | None = None,
    ) -> dict:
        """List WRDS libraries allowed by the selected profile."""
        return list_wrds_libraries(
            profile=profile,
            include_table_counts=include_table_counts,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="List accessible WRDS tables",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def list_accessible_wrds_tables(
        library: str,
        profile: str = "wrds_readonly",
        search: str | None = None,
        limit: int = 500,
        policy_path: str | None = None,
    ) -> dict:
        """List tables in one allowed WRDS library, optionally filtered by name."""
        return list_wrds_tables(
            library=library,
            profile=profile,
            search=search,
            limit=limit,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="Describe accessible WRDS table",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def describe_accessible_wrds_table(
        library: str,
        table: str,
        profile: str = "wrds_readonly",
        policy_path: str | None = None,
    ) -> dict:
        """Describe live WRDS columns for one allowed library.table."""
        return describe_wrds_table(
            library=library,
            table=table,
            profile=profile,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="Probe WRDS table access",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def probe_accessible_wrds_tables(
        profile: str = "wrds_readonly",
        library: str | None = None,
        search: str | None = None,
        limit: int = 5000,
        policy_path: str | None = None,
    ) -> dict:
        """Check SELECT privilege for visible WRDS tables without reading table rows."""
        return probe_wrds_table_access(
            profile=profile,
            library=library,
            search=search,
            limit=limit,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="Materialize accessible WRDS table",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=False,
            openWorldHint=True,
        ),
    )
    def materialize_accessible_wrds_table(
        library: str,
        table: str,
        columns: list[str] | None = None,
        filters: list[dict] | None = None,
        limit: int = 1000,
        profile: str = "wrds_readonly",
        output_dir: str | None = None,
        policy_path: str | None = None,
    ) -> dict:
        """Write a guarded Parquet extract from an allowed WRDS table using structured filters."""
        return materialize_wrds_table(
            library=library,
            table=table,
            columns=columns,
            filters=filters,
            limit=limit,
            profile=profile,
            output_dir=output_dir,
            policy_path=policy_path,
        )

    @mcp.tool(
        title="Plan WRDS research request",
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=False,
        ),
    )
    def plan_wrds_research_request(
        request: str,
        profile: str = "wrds_readonly",
        policy_path: str | None = None,
    ) -> dict:
        """Parse a request and return the approved dataset, security, SQL template, and next tool call."""
        return plan_research_request(request=request, profile=profile, policy_path=policy_path)

    @mcp.tool(
        title="Materialize WRDS research data",
        annotations=ToolAnnotations(
            readOnlyHint=False,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def get_research_data(
        request: str,
        profile: str = "demo",
        output_dir: str | None = None,
        source: str | None = None,
        policy_path: str | None = None,
    ) -> dict:
        """Parse a research request, fetch approved CRSP returns, and write parquet."""
        return run_research_request(
            request,
            output_dir=output_dir,
            source=source,
            profile=profile,
            policy_path=policy_path,
        ).as_dict()

    return mcp


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
