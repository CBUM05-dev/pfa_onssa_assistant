from onssa_ai.core.config import get_settings


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.models.embedding_model == "BAAI/bge-m3"
    assert settings.qdrant.collection_name == "onssa_food_safety_regulations"
    assert settings.retrieval.query_routing_rules
