"""Answer validation placeholder."""


class AnswerValidator:
    """Validate answer citation discipline before returning to API callers."""

    def validate(self, answer: str) -> bool:
        return bool(answer.strip())
