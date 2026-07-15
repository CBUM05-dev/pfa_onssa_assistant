# Step 4 - Validation corpus et chunking

## Objectif PRD

Cette etape transforme le corpus vertical slice en chunks citation-safe.

Elle garantit que chaque chunk conserve assez de metadata pour permettre:

- retrieval filtre par domaine ONSSA;
- citations traçables;
- refus RAG si aucune preuve n'est retrouvee;
- indexation Qdrant propre;
- evaluation document/page/chunk.

## Entree

```text
data/corpus/knowledge_corpus.json
```

Le corpus doit representer le vertical slice courant:

```text
Reglementation
-> Reglementation Transversale
-> Securite Sanitaire
```

Verification attendue avant cette etape:

```text
19 documents
domain = reglementation_transversale
subdomain = securite_sanitaire
```

## Sorties

```text
data/processed/chunks/chunks.jsonl
data/processed/chunks/chunking_report.json
```

`chunks.jsonl` contient un chunk par ligne.

## Commande

```bash
python scripts/build_chunks.py --config configs/chunking.yaml
```

Ou:

```bash
make build-chunks
```

## Fichiers crees ou modifies

### `configs/chunking.yaml`

Configure:

- corpus source;
- fichier de sortie chunks;
- fichier rapport;
- taille max d'un chunk;
- overlap;
- taille minimale;
- domain/subdomain requis;
- refus des documents `unclassified`.

### `scripts/build_chunks.py`

Point d'entree CLI.

Il orchestre:

```text
load corpus
-> validate corpus
-> build chunks
-> write chunks.jsonl
-> write chunking_report.json
```

### `src/onssa_ai/corpus/validator.py`

Verifie les invariants de production:

- document ids uniques;
- titre present;
- `source_url` present;
- `source_hash` present;
- pages presentes;
- texte non vide;
- pas de documents `unclassified` si interdit;
- domain/subdomain attendus;
- pages non dupliquees.

### `src/onssa_ai/corpus/chunker.py`

Decoupe avec une strategie hybride `structure_aware`.

Ordre de preference:

```text
1. Detecter les unites reglementaires: Article, Chapitre, Section, Titre, Annexe
2. Garder l'unite complete si elle tient dans max_chars
3. Si l'unite est trop longue, la split avec overlap
4. Si aucune structure n'est detectee, fallback page-level
5. Si une page est trop longue, fallback character split avec overlap
```

Chaque chunk garde:

- `document_id`;
- `document_title`;
- `source_url`;
- `local_path`;
- `source_hash`;
- `page_start`;
- `page_end`;
- `page_numbers`;
- `vertical`;
- `domain`;
- `subdomain`;
- `site_hierarchy`;
- `site_parent_url`;
- `site_sub_subdomain`;
- `site_sub_subdomain_display`;
- `chunk_type`;
- `section_title`;
- `structure_path`;
- `chunk_hash`;
- `citation_label`.

### `src/onssa_ai/schemas/chunk.py`

Schema Pydantic du chunk.

C'est le contrat entre:

```text
chunking
-> embeddings
-> Qdrant
-> retrieval
-> citations
```

## Pourquoi JSONL

`chunks.jsonl` est choisi parce que:

- chaque chunk est une ligne independante;
- facile a streamer pour embeddings;
- facile a reprendre apres erreur;
- compatible avec batch indexing Qdrant.

## Verification apres execution

Verifier le rapport:

```bash
code data/processed/chunks/chunking_report.json
```

Verifier le nombre de chunks:

```bash
python -c "import json; print(sum(1 for _ in open('data/processed/chunks/chunks.jsonl', encoding='utf-8')))"
```

Voir un chunk:

```bash
python -c "import json; row=json.loads(open('data/processed/chunks/chunks.jsonl', encoding='utf-8').readline()); print(row.keys()); print(row['metadata']); print(row['text'][:500])"
```

## Relation avec les prochaines etapes

```text
chunks.jsonl
-> embeddings BAAI/bge-m3
-> Qdrant
-> retriever
-> reranker
-> prompt builder
-> RAG answer with citations
```

## Etat attendu avant Step 5

Avant embeddings, il faut avoir:

```text
data/processed/chunks/chunks.jsonl
data/processed/chunks/chunking_report.json
```

et chaque chunk doit avoir une citation traçable.

## Note de conception

Le chunking n'est pas un simple split par caractères. Pour les textes reglementaires ONSSA, il doit respecter autant que possible les frontieres juridiques:

```text
Article
Chapitre
Section
Titre
Annexe
```

Le split par caractères reste seulement un fallback pour les blocs trop longs ou non structures.

La detection est volontairement stricte:

```text
Article / Chapitre / Section / Titre / Annexe
```

ne sont consideres comme frontieres que lorsqu'ils apparaissent comme titres structurels. Le mot `article` dans une phrase comme `notamment son article...` ne doit pas couper le chunk.
