"""Batching helpers."""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def batched(items: list[T], batch_size: int) -> Iterable[list[T]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]
