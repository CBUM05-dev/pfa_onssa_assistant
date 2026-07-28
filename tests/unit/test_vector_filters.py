from onssa_ai.schemas.retrieval import RetrievalFilters
from onssa_ai.vectorstore.filters import build_payload_filter


def test_payload_filter_includes_site_sub_subdomain() -> None:
    qdrant_filter = build_payload_filter(
        RetrievalFilters(
            vertical="institutionnel",
            domain="onssa",
            subdomain="presentation",
            site_sub_subdomain="glossaire",
        )
    )

    assert qdrant_filter is not None
    keys = {condition.key for condition in qdrant_filter.must or []}
    assert "site_sub_subdomain" in keys
