"""Generation policy configuration."""

from pydantic import BaseModel


class GenerationOptions(BaseModel):
    max_tokens: int = 1024
    temperature: float = 0.1
