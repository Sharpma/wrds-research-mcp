from wrds_research_mcp.library_descriptions import describe_library, library_search_text


def test_describe_known_library_guides_crsp() -> None:
    guidance = describe_library("crsp", detailed=True)

    assert guidance["title"] == "CRSP"
    assert "stock returns" in guidance["topics"]
    assert guidance["guidance_confidence"] == "medium"
    assert "recommended_next_tools" in guidance["detail"]


def test_describe_unknown_library_has_fallback_guidance() -> None:
    guidance = describe_library("custom_feed", detailed=False)

    assert guidance["library"] == "custom_feed"
    assert guidance["guidance_confidence"] == "low"
    assert "inspect" in guidance["agent_hint"].lower()


def test_library_search_text_includes_topics_and_hint() -> None:
    guidance = describe_library("ibes")

    text = library_search_text(guidance)

    assert "analyst" in text
    assert "forecast" in text
