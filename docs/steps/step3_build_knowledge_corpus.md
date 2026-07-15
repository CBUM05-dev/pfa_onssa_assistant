# Step 3 - Build knowledge_corpus.json

## Objectif PRD

Cette etape transforme les sources ONSSA synchronisees en corpus canonique exploitable par la suite du pipeline IA.

Elle respecte la contrainte centrale du PRD:

```text
La connaissance reglementaire vient des documents ONSSA recuperes localement.
Le modele ne doit pas memoriser les reglements.
La retrieval layer sera responsable de la connaissance.
```

## Entrees

Cette etape lit:

```text
data/sources/onssa_manifest.json
data/raw/pdfs/onssa/*.pdf
data/raw/pages/onssa/*.html
```

Le manifest donne:

- URL source;
- type `pdf` ou `page`;
- chemin local;
- hash SHA-256;
- statut;
- page parent;
- derniere date de detection.

## Sorties

Cette etape genere:

```text
data/corpus/knowledge_corpus.json
data/corpus/validation_reports/knowledge_corpus_build_report.json
```

## Commande principale

Depuis la racine du projet:

```bash
python scripts/build_knowledge_corpus.py --config configs/corpus.yaml
```

Ou:

```bash
make build-corpus
```

## Options utiles

Inclure aussi les pages HTML:

```bash
python scripts/build_knowledge_corpus.py --config configs/corpus.yaml --include-pages
```

Inclure toutes les sources processables sans filtrage first slice:

```bash
python scripts/build_knowledge_corpus.py --config configs/corpus.yaml --include-all
```

Inclure tout:

```bash
python scripts/build_knowledge_corpus.py --config configs/corpus.yaml --include-pages --include-all
```

## Fichiers crees dans cette etape

### `configs/corpus.yaml`

Configure le build du corpus:

- manifest source;
- chemin de sortie du corpus;
- chemin du rapport;
- inclusion ou non des pages HTML;
- inclusion ou non de toutes les sources;
- taille minimale du texte extrait;
- vertical/domain/subdomain.
- chemin vers `configs/taxonomy.yaml`.

### `configs/taxonomy.yaml`

Declare la taxonomie du site ONSSA.

Exemple:

```text
Reglementation
-> Reglementation Transversale
-> Securite Sanitaire
```

Le builder utilise cette taxonomie avec `parent_url` du manifest pour classifier les documents selon leur page d'origine sur le site.

### `scripts/build_knowledge_corpus.py`

Point d'entree CLI.

Il charge `configs/corpus.yaml`, applique les options CLI, lance `CorpusBuilder`, puis imprime le rapport JSON.

### `src/onssa_ai/ingestion/pdf_extractor.py`

Extrait le texte des PDF page par page avec `pypdf`.

Chaque page devient:

```json
{
  "page_number": 1,
  "text": "..."
}
```

### `src/onssa_ai/ingestion/html_extractor.py`

Extrait le texte lisible des pages HTML telechargees.

Par defaut les pages HTML ne sont pas incluses dans le corpus, mais l'option `--include-pages` les active.

### `src/onssa_ai/ingestion/source_classifier.py`

Classe les sources avec la taxonomie du site ONSSA:

```text
Regulation -> Transversal Regulation -> Food Safety
```

Il utilise d'abord la page parent du document dans `data/sources/onssa_manifest.json`.

Important:

- Les documents extraits de `/reglementation/reglementation-transversale/securite-sanitaire/` recoivent `domain=reglementation_transversale` et `subdomain=securite_sanitaire`.
- Les documents inclus en mode large `--include-all` recoivent leur domaine ONSSA si une regle de taxonomie matche.
- Les documents sans regle restent `domain=unclassified` et `subdomain=unclassified`.
- La metadata garde `site_hierarchy`, `site_parent_url`, `site_sub_subdomain`, `classification_reason`, `classification_confidence`, `matched_keywords` et `needs_review`.

### `src/onssa_ai/ingestion/corpus_builder.py`

Orchestre:

```text
manifest
-> classification
-> extraction PDF/HTML
-> document_id stable
-> metadata source
-> knowledge_corpus.json
-> build report
```

### `src/onssa_ai/schemas/corpus.py`

Definit la structure canonique:

```text
KnowledgeCorpus
-> CorpusDocument[]
-> CorpusPage[]
```

## Structure d'un document du corpus

Chaque document contient:

```text
document_id
title
source_url
local_path
source_hash
document_type
language
vertical
domain
subdomain
pages
text
metadata
```

La metadata contient aussi la trace de la hierarchie site:

```text
metadata.site_hierarchy
metadata.site_parent_url
metadata.site_matched_rule
metadata.site_sub_subdomain
metadata.site_sub_subdomain_display
```

## Relation avec les autres etapes

```text
Step 2 - sync ONSSA sources
-> Step 3 - build knowledge_corpus.json
-> Step 4 - validate corpus + chunking
-> Step 5 - embeddings bge-m3
-> Step 6 - Qdrant indexing
-> Step 7 - RAG API
```

## Verification apres execution

Verifier que le corpus existe:

```bash
dir data\corpus\knowledge_corpus.json
```

Lire le rapport:

```bash
code data\corpus\validation_reports\knowledge_corpus_build_report.json
```

Verifier le nombre de documents:

```bash
python -c "import json; d=json.load(open('data/corpus/knowledge_corpus.json', encoding='utf-8')); print(len(d['documents']))"
```

## Decision avant l'etape suivante

Si le nombre de documents est trop faible, lancer avec:

```bash
python scripts/build_knowledge_corpus.py --config configs/corpus.yaml --include-all
```

Dans ce mode, les documents hors vertical slice recoivent leur domaine reel si `configs/taxonomy.yaml` contient la regle correspondante. Sinon ils restent `unclassified`.

Important pour la suite:

```text
configs/taxonomy.yaml ne couvre pas encore toutes les pages ONSSA.
Le vertical slice securite-sanitaire est couvert.
Le corpus global --include-all peut donc contenir des documents unclassified.
Ces documents sont exploitables mais leur domaine exact doit etre ajoute progressivement dans la taxonomie.
```

Etat valide pour continuer le PRD actuel:

```text
included_documents = 19
first_slice_documents = 19
domain/subdomain = reglementation_transversale / securite_sanitaire
```

Si les pages HTML contiennent des informations utiles, lancer avec:

```bash
python scripts/build_knowledge_corpus.py --config configs/corpus.yaml --include-pages
```

Quand le corpus est satisfaisant, passer a l'etape 4:

```text
validation corpus + chunking
```

## Raffinements connus

Lire aussi:

```text
docs/refinement_backlog.md
```
