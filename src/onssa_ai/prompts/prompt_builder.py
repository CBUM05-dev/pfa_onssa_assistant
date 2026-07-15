"""Prompt construction for grounded regulatory answers."""

from onssa_ai.schemas.retrieval import RetrievedChunk


class PromptBuilder:
    """Build prompts that force evidence-grounded answers with citations."""

    def build(self, question: str, evidence: list[RetrievedChunk]) -> str:
        evidence_blocks = "\n\n".join(
            f"[{item.chunk.chunk_id}] {item.chunk.text}" for item in evidence
        )
        return (
            "You are an ONSSA regulatory assistant. Answer only from the provided evidence. "
            "If the evidence is insufficient, say that you cannot answer reliably.\n\n"
            f"Question:\n{question}\n\nEvidence:\n{evidence_blocks}\n\nAnswer with citations:"
        )
