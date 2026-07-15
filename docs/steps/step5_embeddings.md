# Step 5 - Embeddings BAAI/bge-m3

## Objectif PRD

Cette etape transforme `chunks.jsonl` en vecteurs denses locaux avec `BAAI/bge-m3`.

Contraintes respectees:

- pas d'OpenAI API;
- pas de service cloud d'embeddings;
- execution on-premise;
- conservation stricte des metadonnees de citation;
- dimension compatible Qdrant: `1024`;
- sortie audit-able avant indexation.

## Entree

```text
data/processed/chunks/chunks.jsonl
```

Chaque ligne doit respecter le schema `KnowledgeChunk` et contenir au minimum:

- `chunk_id`;
- `text`;
- `metadata.document_id`;
- `metadata.source_url`;
- `metadata.page_numbers`;
- `metadata.chunk_hash`;
- `metadata.citation_label`.

## Sorties

```text
data/processed/embeddings/chunk_embeddings.jsonl
data/processed/embeddings/embedding_report.json
```

`chunk_embeddings.jsonl` contient un chunk embedde par ligne:

```text
chunk_id
text
metadata
embedding
embedding_model
embedding_dimension
```

Les metadonnees sont conservees pour que les prochaines etapes puissent imposer:

```text
retrieval -> evidence -> citations -> refus si aucune preuve
```

## Commande

```bash
python scripts/build_embeddings.py --config configs/embeddings.yaml
```

Ou:

```bash
make build-embeddings
```

## Fichiers crees ou modifies

### `configs/embeddings.yaml`

Configure:

- fichier d'entree chunks;
- fichier de sortie embeddings;
- rapport;
- modele `BAAI/bge-m3`;
- device local;
- batch size;
- dimension attendue `1024`;
- normalisation cosine;
- mode `local_files_only`.

### `src/onssa_ai/embeddings/bge_m3.py`

Adapter local pour `sentence-transformers`.

Le modele est charge paresseusement uniquement quand `embed_texts()` est appele. Cela evite que l'API backend charge les dependances ML au demarrage.

En mode production on-premise, `local_files_only: true` active:

```text
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

Le modele doit donc etre present dans le cache local ou dans `data/models/base`.

### `scripts/build_embeddings.py`

Point d'entree CLI.

Pipeline:

```text
load config
-> read chunks.jsonl
-> validate KnowledgeChunk
-> reject duplicate chunk_id
-> embed by batch with BAAI/bge-m3
-> verify vector dimension = 1024
-> write chunk_embeddings.jsonl
-> write embedding_report.json
```

### `src/onssa_ai/schemas/embedding.py`

Schema Pydantic de l'artefact d'embedding.

Il garde le texte et les metadonnees avec le vecteur pour permettre une indexation Qdrant reproductible.

## Pre-requis local

Installer les dependances ML dans l'environnement local/on-premise:

```bash
pip install -e .[ml]
```

Le modele doit etre disponible localement avant execution offline:

```text
BAAI/bge-m3
```

Si le serveur n'a pas acces a Internet, precharger le modele dans un environnement controle puis copier le cache Hugging Face ou un dossier modele local sous:

```text
data/models/base
```

## Verification apres execution

Verifier le rapport:

```bash
code data/processed/embeddings/embedding_report.json
```

Compter les embeddings:

```bash
python -c "import json; print(sum(1 for _ in open('data/processed/embeddings/chunk_embeddings.jsonl', encoding='utf-8')))"
```

Verifier une ligne:

```bash
python -c "import json; row=json.loads(open('data/processed/embeddings/chunk_embeddings.jsonl', encoding='utf-8').readline()); print(row['chunk_id']); print(row['embedding_model']); print(len(row['embedding'])); print(row['metadata']['citation_label'])"
```

## Relation avec Qdrant

La configuration Qdrant attend:

```text
collection_name = onssa_food_safety_regulations
vector_size = 1024
distance = cosine
```

Les embeddings sont normalises pour la recherche cosine.

La prochaine etape doit indexer:

- vecteur: `embedding`;
- id stable: `chunk_id`;
- payload: `metadata` + champs utiles de ranking/debug.

## Regle RAG a conserver

Cette etape ne genere aucune reponse utilisateur.

Les contraintes RAG restent pour les etapes retrieval/generation:

```text
aucune evidence -> refus
evidence retrouvee -> reponse avec citations obligatoires
```
