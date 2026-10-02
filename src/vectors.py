from __future__ import annotations

import math

def dot(a: list[float], b: list[float]) -> float:
    return sum(left * right for left, right in zip(a, b))
def norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))
def normalize_vector(vector: list[float]) -> list[float]:
    denominator = norm(vector)
    if not denominator:
        return [0.0 for _ in vector]
    return [value / denominator for value in vector]
def cosine_similarity(a: list[float], b: list[float]) -> float:
    denominator = norm(a) * norm(b)
    if not denominator:
        return 0.0
    return dot(a, b) / denominator
