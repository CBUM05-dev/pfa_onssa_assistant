# Refinement Backlog

This file records known limitations that must be refined before production release.

## 1. Source Classification

Current status:

- Source classification is deterministic and primarily based on ONSSA site taxonomy in `configs/taxonomy.yaml`.
- It uses `parent_url` from `data/sources/onssa_manifest.json`.
- Keyword matching is secondary metadata, not the source of truth for domain/subdomain.
- It does not yet inspect full extracted text to classify regulatory domain/subdomain.
- `configs/taxonomy.yaml` currently covers the first vertical slice and an initial set of ONSSA regulatory pages, but it does not yet cover every page discovered by the crawler.

Risk:

- Some documents can be relevant but missed.
- Some documents can be included in the first slice with only medium confidence.
- In broad corpus mode, documents whose parent page is not yet represented in `configs/taxonomy.yaml` remain `unclassified/unclassified`.

Current mitigation:

- `domain` and `subdomain` are assigned from ONSSA site hierarchy.
- Broad corpus mode keeps non-matching documents as `unclassified/unclassified` only when no taxonomy rule matches.
- Every document has metadata:
  - `site_hierarchy`
  - `site_parent_url`
  - `site_matched_rule`
  - `site_sub_subdomain`
  - `classification_reason`
  - `classification_confidence`
  - `matched_keywords`
  - `needs_review`
  - `regulation_type`

Future refinement:

- Classify using extracted text, not only URL/title.
- Extend the taxonomy file for every ONSSA regulatory page.
- Add a periodic taxonomy audit command that reports discovered parent URLs not covered by `configs/taxonomy.yaml`.
- Add manual review overrides in a YAML file.
- Add tests with known ONSSA documents and expected domain/subdomain.

## 2. PDF Extraction Quality

Current status:

- PDF extraction uses `pypdf`.
- Some PDFs emit encoding warnings.

Risk:

- Some old PDFs can produce incomplete or noisy text.
- Scanned PDFs may require OCR.

Future refinement:

- Add PyMuPDF fallback.
- Add OCR fallback for scanned PDFs.
- Add extraction quality score per document.
- Flag documents with low extracted text density.

## 3. Corpus Validation

Current status:

- `knowledge_corpus.json` is generated with source traceability.
- Strict validation and structure-aware chunking are implemented for the current vertical slice.
- The chunker detects regulatory markers such as Article, Chapitre, Section, Titre and Annexe.
- Oversized regulatory units are split with overlap, preserving citation metadata.

Future refinement:

- Validate document ids, source hashes, page text and metadata.
- Detect duplicate documents.
- Detect empty or suspicious pages.
- Add tests for edge cases in old ONSSA PDF extraction.
- Add OCR-aware chunking when scanned PDFs are introduced.

## 4. Citation Traceability

Current status:

- Document-level and page-level metadata exist.

Future refinement:

- Every chunk must preserve source URL, file path, source hash and page range.
- RAG answers must cite retrieved chunks only.
- The API must refuse answers without retrieved evidence.
