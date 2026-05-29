from wrds_research_mcp.dictionary import read_data_dictionary, search_data_dictionary
from wrds_research_mcp.dictionary import _string_or_none


def test_read_catalog_dictionary_exposes_allowed_monthly_table() -> None:
    dictionary = read_data_dictionary(
        profile="wrds_readonly",
        dataset="crsp_monthly_returns",
        source="catalog",
    )

    dataset = dictionary["datasets"]["crsp_monthly_returns"]
    assert dataset["frequency"] == "monthly"
    assert "crsp.stkmthsecuritydata" in dataset["tables"]


def test_search_catalog_dictionary_finds_return_field() -> None:
    result = search_data_dictionary(
        "return",
        profile="wrds_readonly",
        dataset="crsp_monthly_returns",
        source="catalog",
    )

    assert any(
        match["kind"] == "column" and match["column"]["name"] == "ret"
        for match in result["matches"]
    )


def test_dictionary_type_values_are_serializable_strings() -> None:
    assert _string_or_none("NUMERIC(10, 6)") == "NUMERIC(10, 6)"
    assert _string_or_none(None) is None
