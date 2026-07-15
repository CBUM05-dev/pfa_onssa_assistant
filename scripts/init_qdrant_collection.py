"""Initialize the Qdrant collection."""

from onssa_ai.core.config import get_settings
from onssa_ai.vectorstore.collection_manager import QdrantCollectionManager
from onssa_ai.vectorstore.qdrant_client import build_qdrant_client


def main() -> None:
    settings = get_settings()
    client = build_qdrant_client(settings.qdrant)
    QdrantCollectionManager(client, settings.qdrant).ensure_collection()
    print(f"Collection ready: {settings.qdrant.collection_name}")


if __name__ == "__main__":
    main()
