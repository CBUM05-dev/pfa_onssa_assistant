"""Export model artifacts for vLLM."""

from onssa_ai.finetuning.export import ModelExporter


def main() -> None:
    ModelExporter().export()


if __name__ == "__main__":
    main()
