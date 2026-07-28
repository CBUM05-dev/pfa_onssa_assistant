"""Qdrant payload filter construction."""

from qdrant_client.http import models

from onssa_ai.schemas.retrieval import RetrievalFilters


def build_payload_filter(filters: RetrievalFilters) -> models.Filter | None:
    conditions: list[models.FieldCondition] = []
    values = {
        "vertical": filters.vertical,
        "domain": filters.domain,
        "subdomain": filters.subdomain,
        "site_sub_subdomain": filters.site_sub_subdomain,
        "document_id": filters.document_id,
        "language": filters.language,
    }
    for key, value in values.items():
        if value is not None:
            conditions.append(
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                )
            )
    if not conditions:
        return None
    return models.Filter(must=conditions)
