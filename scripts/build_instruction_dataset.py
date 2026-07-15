"""Build behavior-focused instruction dataset."""

from onssa_ai.finetuning.dataset_builder import InstructionDatasetBuilder


def main() -> None:
    InstructionDatasetBuilder().build()


if __name__ == "__main__":
    main()
