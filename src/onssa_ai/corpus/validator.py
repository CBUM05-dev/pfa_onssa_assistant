"""Corpus validation rules."""

from collections import Counter

from onssa_ai.core.exceptions import CorpusValidationError
from onssa_ai.schemas.corpus import KnowledgeCorpus


class CorpusValidator:
    """Validate corpus invariants required for citation-safe RAG."""

    def validate(
        self,
        corpus: KnowledgeCorpus,
        require_domain: str | None = None,
        require_subdomain: str | None = None,
        fail_on_unclassified: bool = True,
    ) -> None:
        document_ids = [document.document_id for document in corpus.documents]
        duplicates = {doc_id for doc_id, count in Counter(document_ids).items() if count > 1}
        if duplicates:
            raise CorpusValidationError(f"Duplicate document ids: {sorted(duplicates)}")
        for document in corpus.documents:
            if not document.title.strip():
                raise CorpusValidationError(f"Document {document.document_id} has empty title")
            if not document.source_url:
                raise CorpusValidationError(f"Document {document.document_id} has no source_url")
            if not document.source_hash:
                raise CorpusValidationError(f"Document {document.document_id} has no source_hash")
            if not document.pages:
                raise CorpusValidationError(f"Document {document.document_id} has no pages")
            if not (document.text or "").strip():
                raise CorpusValidationError(f"Document {document.document_id} has empty text")
            if fail_on_unclassified and (
                document.domain == "unclassified" or document.subdomain == "unclassified"
            ):
                raise CorpusValidationError(f"Document {document.document_id} is unclassified")
            if require_domain and document.domain != require_domain:
                raise CorpusValidationError(
                    f"Document {document.document_id} domain={document.domain}, "
                    f"expected {require_domain}"
                )
            if require_subdomain and document.subdomain != require_subdomain:
                raise CorpusValidationError(
                    f"Document {document.document_id} subdomain={document.subdomain}, "
                    f"expected {require_subdomain}"
                )
            page_numbers = [page.page_number for page in document.pages]
            if len(page_numbers) != len(set(page_numbers)):
                raise CorpusValidationError(f"Document {document.document_id} has duplicate pages")
            for page in document.pages:
                if page.page_number < 1:
                    raise CorpusValidationError(
                        f"Document {document.document_id} has invalid page {page.page_number}"
                    )
                if not page.text.strip():
                    raise CorpusValidationError(
                        f"Document {document.document_id} page {page.page_number} is empty"
                    )
