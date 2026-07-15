# Step 1 - Architecture et scaffold production

## Objectif

Cette etape pose la structure de base du service IA ONSSA.

Elle ne contient pas encore le vrai pipeline RAG complet. Elle definit les dossiers, les contrats Python, les configurations, les points d'entree API, les scripts CLI, Docker et la documentation.

## Fichiers principaux a lire

1. `README.md`
2. `docs/architecture.md`
3. `pyproject.toml`
4. `configs/app.yaml`
5. `configs/models.yaml`
6. `configs/retrieval.yaml`
7. `src/onssa_ai/core/config.py`
8. `src/onssa_ai/schemas/`
9. `src/onssa_ai/rag/service.py`
10. `src/onssa_ai/api/app.py`

## Role des fichiers

### `README.md`

Explique le but du projet, les contraintes souveraines, le pipeline cible et le premier vertical slice.

### `pyproject.toml`

Declare le projet Python:

- version Python cible;
- dependances;
- dependances ML optionnelles;
- outils de test, lint et typage;
- configuration pytest, ruff et mypy.

### `configs/*.yaml`

Contient les parametres qui ne doivent pas etre hardcodes:

- chemins des donnees;
- modeles;
- Qdrant;
- retrieval;
- evaluation;
- fine-tuning;
- logs.

### `src/onssa_ai/core/config.py`

Charge les fichiers YAML et les valide avec Pydantic.

Relation:

```text
configs/*.yaml -> core/config.py -> tous les services Python
```

### `src/onssa_ai/schemas/`

Contient les schemas Pydantic:

- corpus;
- chunks;
- citations;
- retrieval;
- RAG;
- API;
- evaluation.

Ces schemas sont les contrats internes entre modules.

### `src/onssa_ai/rag/service.py`

Montre l'orchestration cible:

```text
question
-> retriever
-> reranker
-> evidence policy
-> prompt builder
-> LLM client
-> citation builder
-> response API
```

### `src/onssa_ai/api/`

Expose le service via FastAPI pour la plateforme ONSSA existante.

Endpoints actuels:

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `POST /api/v1/rag/answer`
- `POST /api/v1/search`

Les endpoints RAG et search sont encore des placeholders.

### `deployment/`

Prepare le deploiement:

- Dockerfile API;
- Dockerfile worker;
- Dockerfile vLLM;
- docker-compose dev/prod;
- Nginx.

### `monitoring/`

Prepare Prometheus, Grafana et les alertes.

## Etat de l'etape

Termine:

- structure projet;
- configs;
- schemas;
- API skeleton;
- RAG skeleton;
- Docker/monitoring skeleton;
- documentation de base;
- compilation Python valide.

Pas encore fait:

- extraction automatique des sources ONSSA;
- validation reelle de `knowledge_corpus.json`;
- chunking robuste;
- embeddings;
- Qdrant indexing;
- retrieval;
- reranking;
- generation LLM reelle;
- evaluation complete.

## Prochaine etape

Lire `step2_source_sync.md`.
