"""Train QLoRA adapter."""

from onssa_ai.finetuning.trainer import QloraTrainer


def main() -> None:
    QloraTrainer().train()


if __name__ == "__main__":
    main()
