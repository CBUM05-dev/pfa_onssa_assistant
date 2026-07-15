"""Run evaluation suite."""

from onssa_ai.evaluation.runner import EvaluationRunner


def main() -> None:
    EvaluationRunner().run()


if __name__ == "__main__":
    main()
