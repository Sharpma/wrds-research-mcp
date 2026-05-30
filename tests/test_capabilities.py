from wrds_research_mcp.capabilities import (
    get_dataset_contract,
    list_datasets,
    list_permission_profiles,
    plan_research_request,
)


def test_list_permission_profiles_exposes_wrds_readonly() -> None:
    profiles = list_permission_profiles()

    assert sorted(profiles["profiles"]) == ["wrds_readonly"]
    assert profiles["profiles"]["wrds_readonly"]["source"] == "wrds"
    assert profiles["profiles"]["wrds_readonly"]["allowed_libraries"] == ["*"]
    assert "allowed_curated_workflows" in profiles["profiles"]["wrds_readonly"]


def test_list_datasets_exposes_monthly_returns() -> None:
    datasets = list_datasets(profile="wrds_readonly")

    assert datasets["catalog_scope"] == "curated_research_workflows_only"
    assert "crsp_monthly_returns" in datasets["datasets"]
    assert "crsp_monthly_returns" in datasets["curated_research_workflows"]
    assert datasets["datasets"]["crsp_monthly_returns"]["frequency"] == "monthly"
    assert datasets["datasets"]["crsp_monthly_returns"]["kind"] == "curated_research_workflow"


def test_describe_monthly_dataset_contract() -> None:
    contract = get_dataset_contract("crsp_monthly_returns", profile="wrds_readonly")

    assert contract["kind"] == "curated_research_workflow"
    assert "not the full WRDS database catalog" in contract["scope_note"]
    assert contract["tables"] == ["crsp.stkmthsecuritydata"]
    assert contract["frequency"] == "monthly"
    assert "ret" in contract["fields"]
    assert contract["execution_tool"] == "get_research_data"


def test_plan_monthly_research_request() -> None:
    plan = plan_research_request(
        "我想获取苹果公司股票2025年的月度收益率数据",
        profile="wrds_readonly",
    )

    assert plan["request"]["dataset"] == "crsp_monthly_returns"
    assert plan["request"]["frequency"] == "monthly"
    assert plan["query_plan"]["template_id"] == "crsp_monthly_returns_v1"
    assert plan["next_step"]["tool"] == "get_research_data"
