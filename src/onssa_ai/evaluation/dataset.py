"""Evaluation dataset loading."""

import json
from pathlib import Path

from onssa_ai.schemas.evaluation import GoldenQuestion


def load_golden_questions(path: Path) -> list[GoldenQuestion]:
    questions: list[GoldenQuestion] = []
    if not path.exists():
        return questions
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                questions.append(GoldenQuestion.model_validate(json.loads(line)))
    return questions
