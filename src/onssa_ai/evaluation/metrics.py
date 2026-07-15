"""Evaluation metrics."""


def recall_at_k(expected_ids: set[str], retrieved_ids: list[str], k: int) -> float:
    if not expected_ids:
        return 1.0
    retrieved = set(retrieved_ids[:k])
    return len(expected_ids & retrieved) / len(expected_ids)
