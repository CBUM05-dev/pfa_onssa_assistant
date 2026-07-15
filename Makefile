.PHONY: test lint run-api sync-sources build-corpus build-chunks build-embeddings validate-corpus init-qdrant index-qdrant

test:
	pytest

lint:
	ruff check src tests scripts

run-api:
	uvicorn onssa_ai.api.app:app --host 0.0.0.0 --port 8000

sync-sources:
	python scripts/sync_onssa_sources.py --config configs/sources.yaml

build-corpus:
	python scripts/build_knowledge_corpus.py --config configs/corpus.yaml

build-chunks:
	python scripts/build_chunks.py --config configs/chunking.yaml

build-embeddings:
	python scripts/build_embeddings.py --config configs/embeddings.yaml

validate-corpus:
	python scripts/validate_corpus.py

init-qdrant:
	python scripts/init_qdrant_collection.py

index-qdrant:
	python scripts/index_qdrant.py --embeddings-config configs/embeddings.yaml --qdrant-config configs/qdrant.yaml
