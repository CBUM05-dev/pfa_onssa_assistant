# Step 7 - RAG avec generation Groq pour phase test

## Objectif

Cette etape cable le vertical slice RAG en gardant l'architecture cible:

```text
Question utilisateur
-> embedding de la question avec BAAI/bge-m3
-> recherche vectorielle Qdrant avec filtres metadonnees
-> reranking avec BAAI/bge-reranker-v2-m3
-> prompt RAG avec preuves
-> generation Groq temporaire
-> reponse + citations
```

Groq remplace uniquement le backend de generation `vLLM` pendant la phase de test. Qdrant, les embeddings, le reranker, la politique de preuve et les citations restent obligatoires.

## Fichiers modifies

### `configs/models.yaml`

Le backend temporaire est:

```yaml
models:
  inference_backend: groq
groq:
  base_url: https://api.groq.com/openai/v1
  model: llama-3.1-8b-instant
```

Pour revenir a l'architecture cible, remettre:

```yaml
models:
  inference_backend: vllm
```

### `src/onssa_ai/llm/groq_client.py`

Client HTTP compatible OpenAI Chat Completions pour Groq.

### `src/onssa_ai/llm/factory.py`

Selectionne le client LLM configure:

```text
vllm -> VllmClient
ollama -> OllamaClient
groq -> GroqClient
```

### `src/onssa_ai/retrieval/qdrant_retriever.py`

Interroge Qdrant avec le vecteur de la question et reconstruit les `KnowledgeChunk` depuis le payload.

### `src/onssa_ai/vectorstore/filters.py`

Construit les filtres Qdrant pour:

```text
vertical
domain
subdomain
document_id
language
```

### `src/onssa_ai/reranking/bge_reranker.py`

Charge localement `BAAI/bge-reranker-v2-m3` et trie les chunks retrouves avant generation.

### `src/onssa_ai/api/dependencies.py`

Assemble le pipeline:

```text
QdrantRetriever + BgeReranker + PromptBuilder + GroqClient + CitationBuilder + EvidencePolicy
```

## Preparation

Avant d'appeler Groq, la base vectorielle doit exister:

```powershell
$env:PYTHONPATH="src"
py -3 scripts/build_embeddings.py --config configs/embeddings.yaml
docker compose -f deployment/compose/docker-compose.dev.yml up -d --force-recreate qdrant
py -3 scripts/index_qdrant.py --embeddings-config configs/embeddings.yaml --qdrant-config configs/qdrant.yaml --qdrant-host 127.0.0.1
```

Sur une nouvelle machine, `data/processed/embeddings/chunk_embeddings.jsonl` doit etre genere avant l'indexation Qdrant.

## Test local

```powershell
$env:ONSSA_GROQ_API_KEY="..."
$env:PYTHONPATH="src"
py -3 scripts/run_rag_query.py "Quelle est la base reglementaire de la securite sanitaire des produits alimentaires ?"
```

## Test API

```powershell
$env:ONSSA_GROQ_API_KEY="..."
$env:PYTHONPATH="src"
uvicorn onssa_ai.api.app:app --reload
```

Endpoint:

```text
POST /api/v1/rag/answer
```

## Regle de retour

Ne pas supprimer Qdrant ni le reranker au retour production. Seul le backend de generation doit repasser de `groq` a `vllm`.
