"""QLoRA configuration schema."""

from pydantic import BaseModel


class QloraConfig(BaseModel):
    base_model: str
    output_dir: str
    max_seq_length: int
    lora_r: int
    lora_alpha: int
    lora_dropout: float
