# ONSSA Server Installation - RunPod Test Phase

This procedure installs the current ONSSA service on the ONSSA Ubuntu server while keeping GPU inference on RunPod.

Target architecture:

```text
ONSSA server: FastAPI + Qdrant + embeddings + reranker + citations
RunPod: vLLM OpenAI-compatible endpoint + Qwen3 8B
```

## 1. Server prerequisites

Use Ubuntu Server 24.04 LTS or compatible.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git make rsync
```

Install Docker Engine and the Docker Compose plugin before continuing.

Verify:

```bash
docker version
docker compose version
```

## 2. Copy the project

Do not copy an existing Python virtual environment to the server. Build dependencies fresh from `pyproject.toml`.

Recommended target directory:

```bash
sudo mkdir -p /opt/onssa-ai
sudo chown "$USER":"$USER" /opt/onssa-ai
```

Copy the repository contents to `/opt/onssa-ai`, including:

```text
configs/
data/corpus/
data/processed/
data/models/base/
deployment/
scripts/
src/
pyproject.toml
README.md
```

The `data/models/base/` directory is required because the API uses BGE models in offline mode.

Important: `git clone` alone is not enough for a ready server installation because model and embedding artifacts are ignored by Git. Copy the data artifacts explicitly from the validated machine.

## 3. Configure environment

Create `/opt/onssa-ai/.env` from `.env.onssa-runpod.example`:

```bash
cp .env.onssa-runpod.example .env
nano .env
```

Required values:

```bash
ONSSA_INFERENCE_BACKEND=vllm
ONSSA_VLLM_BASE_URL=https://REPLACE_WITH_RUNPOD_VLLM_HOST
ONSSA_VLLM_MODEL=Qwen/Qwen3-8B-Instruct
ONSSA_VLLM_API_KEY=
```

Use a base URL without `/v1`. The application calls:

```text
<ONSSA_VLLM_BASE_URL>/v1/chat/completions
```

If RunPod protects the endpoint with a bearer token, set `ONSSA_VLLM_API_KEY`.

## 4. Build and start services

```bash
cd /opt/onssa-ai
docker compose -f deployment/compose/docker-compose.onssa-runpod.yml build
docker compose -f deployment/compose/docker-compose.onssa-runpod.yml up -d
```

Check containers:

```bash
docker compose -f deployment/compose/docker-compose.onssa-runpod.yml ps
docker compose -f deployment/compose/docker-compose.onssa-runpod.yml logs --tail=100 api
```

## 5. Initialize Qdrant

If `data/processed/embeddings/chunk_embeddings.jsonl` exists, index it into Qdrant:

```bash
docker compose -f deployment/compose/docker-compose.onssa-runpod.yml exec api \
  python scripts/index_qdrant.py \
  --embeddings-config configs/embeddings.yaml \
  --qdrant-config configs/qdrant.yaml
```

Verify the report:

```bash
cat data/processed/embeddings/qdrant_index_report.json
```

The `indexed_count` must match the embeddings count.

## 6. Smoke tests

Health:

```bash
curl http://localhost/health
```

RunPod connectivity from the API container:

```bash
docker compose -f deployment/compose/docker-compose.onssa-runpod.yml exec api \
  python -c "from onssa_ai.core.config import get_settings; s=get_settings(); print(s.models.inference_backend, s.vllm.base_url, s.vllm.model)"
```

RAG endpoint:

```bash
curl -X POST http://localhost/api/v1/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le delai de la visite sanitaire ?"}'
```

Expected behavior:

- if evidence exists: answer with citations;
- if evidence is insufficient: refusal message;
- no Python dependency error;
- no Qdrant connection error;
- no LLM provider connection error.

## 7. Do not use this compose file for the current phase

Do not start `deployment/compose/docker-compose.prod.yml` during the RunPod phase. It still defines a local `vllm` GPU service and is meant for a future on-premise GPU deployment.
