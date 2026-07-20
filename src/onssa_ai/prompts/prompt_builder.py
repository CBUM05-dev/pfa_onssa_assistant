"""Prompt construction for grounded regulatory answers."""

from onssa_ai.prompts.policies import INSUFFICIENT_EVIDENCE_MESSAGE
from onssa_ai.schemas.retrieval import RetrievedChunk


class PromptBuilder:
    """Build prompts that force evidence-grounded answers with citations."""

    def build(self, question: str, evidence: list[RetrievedChunk]) -> str:
        evidence_blocks = "\n\n".join(
            f"[{item.chunk.chunk_id}] {item.chunk.text}" for item in evidence
        )
        return (
            "You are an ONSSA regulatory assistant. Answer only from the provided evidence.\n"
            "Rules:\n"
            "- If the evidence contains the answer, answer directly and do not include any refusal "
            "or uncertainty sentence.\n"
            "- If the evidence does not contain the answer, return only this sentence: "
            f"{INSUFFICIENT_EVIDENCE_MESSAGE}\n"
            "- Never write a contradictory answer such as 'I cannot answer' followed by an answer.\n"
            "- Quote the relevant article or passage and cite the chunk id in brackets.\n\n"
            f"Question:\n{question}\n\nEvidence:\n{evidence_blocks}\n\nAnswer with citations:"
        )
