# Step 6 - Indexation Qdrant

## Objectif PRD

Cette etape charge les embeddings locaux dans Qdrant pour rendre le corpus ONSSA interrogeable par similarite vectorielle.

Contraintes respectees:

- indexation on-premise;
- ids de points deterministes a partir de `chunk_id`;
- conservation du texte et des metadonnees de citation dans le payload;
- verification de dimension avant upsert;
- rapport d'indexation audit-able.

## Entree

```text
data/processed/embeddings/chunk_embeddings.jsonl
```

Chaque ligne doit respecter le schema `EmbeddedChunk`:

- `chunk_id`;
- `text`;
- `metadata`;
- `embedding`;
- `embedding_model`;
- `embedding_dimension`.

## Sortie

```text
data/processed/embeddings/qdrant_index_report.json
```

Le rapport contient:

- collection cible;
- dimension vectorielle;
- batch size;
- nombre de chunks lus;
- nombre de points indexes.

## Commande

Demarrer Qdrant en local:

```bash
docker compose -f deployment/compose/docker-compose.dev.yml up -d qdrant
```

Indexer les embeddings:

```bash
python scripts/index_qdrant.py --embeddings-config configs/embeddings.yaml --qdrant-config configs/qdrant.yaml
```

Ou:

```bash
make index-qdrant
```

## Fichiers crees ou modifies

### `scripts/index_qdrant.py`

Point d'entree CLI.

Pipeline:

```text
load embeddings config
-> load qdrant config
-> read chunk_embeddings.jsonl
-> validate vector size
-> ensure collection and payload indexes
-> upsert points by batch
-> write qdrant_index_report.json
```

### `src/onssa_ai/vectorstore/indexer.py`

Transforme chaque `EmbeddedChunk` en point Qdrant:

- id Qdrant: UUID deterministe derive de `chunk_id`;
- vector: `embedding`;
- payload: `metadata` + `chunk_id` + `text` + informations du modele d'embedding.

### `src/onssa_ai/vectorstore/collection_manager.py`

Cree la collection si elle n'existe pas et cree les index payload configures:

```text
vertical
domain
subdomain
document_id
regulation_type
language
```

## Verification apres execution

Verifier le rapport:

```bash
code data/processed/embeddings/qdrant_index_report.json
```

Verifier que `indexed_count` correspond au nombre d'embeddings:

```bash
python -c "import json; print(json.load(open('data/processed/embeddings/qdrant_index_report.json'))['indexed_count'])"
```

## Relation avec retrieval

Apres cette etape, le retrieval peut interroger Qdrant sur:

- similarite vectorielle;
- filtres `vertical`, `domain`, `subdomain`;
- payload de citation pour construire les reponses sourcees.

La regle RAG reste:

```text
aucune evidence -> refus
evidence retrouvee -> reponse avec citations obligatoires
```
