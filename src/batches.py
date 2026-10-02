from __future__ import annotations

from typing import Iterable

def batched(items: list[dict], size: int) -> Iterable[list[dict]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
