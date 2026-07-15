# Step 2 - Synchronisation des sources ONSSA

## Objectif

Cette etape ajoute un mecanisme pour consulter regulierement le site ONSSA, detecter les pages et PDF utiles, telecharger les documents, et savoir si une source a change.

Le but est de garder le corpus a jour sans modifier manuellement les fichiers.

## Principe

Le script part d'une liste de pages de depart configurees dans `configs/sources.yaml`.

Il explore les liens autorises, detecte:

- pages HTML;
- fichiers PDF;
- titres;
- URL source;
- date de consultation;
- hash SHA-256 du contenu;
- statut nouveau, modifie ou inchange.

## Fichiers generes ou modifies

### `configs/sources.yaml`

Configure la synchronisation:

- nom de la source;
- URL de depart;
- domaines autorises;
- profondeur maximale;
- dossier de sortie des pages;
- dossier de sortie des PDF;
- fichier manifest.

### `src/onssa_ai/sources/config.py`

Schemas Pydantic pour valider `configs/sources.yaml`.

### `src/onssa_ai/sources/crawler.py`

Explore les pages ONSSA et collecte les liens.

### `src/onssa_ai/sources/downloader.py`

Telecharge les pages HTML et PDF.

### `src/onssa_ai/sources/manifest.py`

Maintient l'etat des sources deja vues:

```text
URL -> chemin local -> hash -> statut -> date de derniere detection
```

### `scripts/sync_onssa_sources.py`

Point d'entree CLI.

Commande cible:

```bash
python scripts/sync_onssa_sources.py --config configs/sources.yaml
```

### `data/raw/pages/onssa/`

Contient les pages HTML telechargees.

### `data/raw/pdfs/onssa/`

Contient les PDF telecharges.

### `data/sources/onssa_manifest.json`

Contient l'historique et les hashes des sources.

## Relation avec le reste du projet

```text
site ONSSA
-> scripts/sync_onssa_sources.py
-> data/raw/pages/onssa/
-> data/raw/pdfs/onssa/
-> data/sources/onssa_manifest.json
-> ingestion pipeline
-> knowledge_corpus.json
-> chunks
-> embeddings
-> Qdrant
-> RAG
```

## Pourquoi un manifest est necessaire

Sans manifest, le systeme ne sait pas:

- si un PDF est nouveau;
- si un PDF existant a ete modifie;
- si une page a disparu;
- quelle URL a produit quel fichier local;
- quand la source a ete consultee.

Le hash SHA-256 permet de detecter une modification meme si le nom du PDF ne change pas.

## Limites importantes

Le site ONSSA peut changer de structure. C'est pour cela que les URLs de depart et les domaines autorises sont dans un fichier YAML, pas dans le code.

La synchronisation telecharge les documents. Elle ne remplace pas encore l'etape d'extraction PDF vers `knowledge_corpus.json`.

## Prochaine etape

Lire `step3_corpus_validation_chunking.md`.
