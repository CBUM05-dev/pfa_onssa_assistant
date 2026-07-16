# Retour apres phase test Groq

Ce fichier trace l'exception temporaire ajoutee pour tester le vertical slice sans GPU LLM.

## Etat actuel du vertical slice

Le projet cible toujours le vertical slice:

```text
regulation -> reglementation_transversale -> securite_sanitaire
```

La phase test branche maintenant:

```text
chunks -> embeddings BAAI/bge-m3 -> Qdrant -> retrieval vectoriel -> BAAI/bge-reranker-v2-m3 -> prompt RAG -> Groq -> reponse + citations
```

Ce chemin conserve l'architecture RAG cible. La seule substitution temporaire est la generation LLM: Groq remplace vLLM/Qwen local pendant la phase de test.

## Exception temporaire

Groq est configure dans `configs/models.yaml` avec:

```yaml
models:
  inference_backend: groq
groq:
  base_url: https://api.groq.com/openai/v1
  model: llama-3.1-8b-instant
```

La cle doit rester hors Git:

```env
ONSSA_GROQ_API_KEY=...
```

## Fichiers ajoutes pour le test

- `src/onssa_ai/llm/groq_client.py`: client Groq compatible OpenAI Chat Completions.
- `src/onssa_ai/llm/factory.py`: selection du backend `vllm`, `ollama` ou `groq`.
- `src/onssa_ai/retrieval/qdrant_retriever.py`: retriever vectoriel Qdrant avec filtres metadata.
- `src/onssa_ai/vectorstore/filters.py`: filtres Qdrant `vertical`, `domain`, `subdomain`, `document_id`, `language`.
- `src/onssa_ai/reranking/bge_reranker.py`: reranking local avec `BAAI/bge-reranker-v2-m3`.
- `scripts/run_rag_query.py`: test local d'une question RAG.

## Preparation obligatoire avant test Groq

La phase Groq ne saute pas les etapes RAG. Il faut d'abord construire et indexer la base vectorielle:

```powershell
$env:PYTHONPATH="src"
py -3 scripts/build_embeddings.py --config configs/embeddings.yaml
docker compose -f deployment/compose/docker-compose.dev.yml up -d --force-recreate qdrant
py -3 scripts/index_qdrant.py --embeddings-config configs/embeddings.yaml --qdrant-config configs/qdrant.yaml --qdrant-host 127.0.0.1
```

Si `data/processed/embeddings/chunk_embeddings.jsonl` n'existe pas encore sur une nouvelle machine, executer `scripts/build_embeddings.py` avant de tester `/rag/answer`.

Les modeles locaux suivants doivent etre disponibles dans le cache local configure par `configs/embeddings.yaml`:

```text
BAAI/bge-m3
BAAI/bge-reranker-v2-m3
```

## Commande de test RAG + Groq

```powershell
$env:ONSSA_GROQ_API_KEY="..."
$env:PYTHONPATH="src"
py -3 scripts/run_rag_query.py "Quelle est la base reglementaire de la securite sanitaire des produits alimentaires ?"
```

Ou via FastAPI:

```powershell
$env:ONSSA_GROQ_API_KEY="..."
$env:PYTHONPATH="src"
uvicorn onssa_ai.api.app:app --reload
```

Endpoint:

```text
POST /api/v1/rag/answer
```

## Retour a l'architecture cible

Quand les ressources GPU et les artefacts modele sont disponibles:

1. Remettre `configs/models.yaml`:

```yaml
models:
  inference_backend: vllm
```

2. Garder `GroqClient` possible pour les tests, mais ne pas l'utiliser en production ONSSA.
3. Garder `QdrantRetriever` et `BgeReranker`: ils font partie de l'architecture cible.
4. Remonter `retrieval.min_retrieval_score` si necessaire apres evaluation.
5. Relancer les etapes:

```text
build_embeddings -> index_qdrant -> retrieve/rerank -> vLLM generation -> evaluation
```

## Points a ne pas oublier

- Groq sert uniquement a la phase de test et de demonstration de la generation.
- Qdrant, les embeddings et le reranking restent dans le chemin principal.
- La connaissance reglementaire doit rester dans le corpus et le retrieval, pas dans le modele.
- Les citations doivent rester obligatoires.
- Le fine-tuning final reste prevu pour le style, le format et le respect des instructions.
