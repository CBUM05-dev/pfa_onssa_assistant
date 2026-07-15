# ONSSA AI Service

Production-oriented, on-premise AI backend service for ONSSA regulatory food-safety assistance.

This repository is structured for the first vertical slice:

```text
Regulation -> Transversal Regulation -> Food Safety
```

The service is designed to be consumed by the existing ONSSA platform through a REST API. It is not a replacement platform and does not depend on external cloud AI APIs.

## Core Pipeline

```text
Documents ONSSA
-> Knowledge Ingestion Pipeline
-> Knowledge Corpus JSON
-> Instruction Dataset + Embeddings
-> QLoRA Fine-Tuning + Qdrant
-> RAG + LLM
-> Response + Citations
-> Evaluation
-> FastAPI + vLLM/Ollama + Docker
-> Existing ONSSA Platform
```

## Non-Negotiable Constraints

- Fully on-premise deployment.
- No OpenAI API or external cloud AI service.
- Regulatory knowledge comes from retrieval, not model memorization.
- RAG must not answer without retrieved evidence.
- Every answer must preserve citation traceability to source documents.
- Fine-tuning is for behavior, style, citation format, and instruction following.

## Initial Development Order

1. Validate `data/corpus/knowledge_corpus.json`.
2. Normalize records into traceable chunks.
3. Build embeddings with `BAAI/bge-m3`.
4. Index chunks into Qdrant.
5. Retrieve and rerank evidence with `BAAI/bge-reranker-v2-m3`.
6. Generate grounded answers with Qwen3 8B Instruct through vLLM.
7. Expose the RAG service through FastAPI.
8. Add evaluation, monitoring, and deployment hardening.

## Step Documentation

Read the project in this order:

1. `docs/steps/step1_architecture_scaffold.md`
2. `docs/steps/step2_source_sync.md`
3. `docs/steps/step3_build_knowledge_corpus.md`
4. `docs/steps/step4_corpus_validation_chunking.md`
