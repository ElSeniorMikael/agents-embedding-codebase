from __future__ import annotations

import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .tokens import tokenize

def path_name_score(chunk: dict, query_tokens: Iterable[str]) -> float:
    path = chunk["path"].lower()
    name = Path(chunk["path"]).stem.lower()
    score = 0.0
    for token in query_tokens:
        if token in name:
            score += 0.7
        elif token in path:
            score += 0.35
    return score
def symbol_match_score(index: dict, chunk: dict, query_tokens: Iterable[str]) -> float:
    return symbol_list_match_score(index.get("symbols", []), chunk, query_tokens)

def symbols_by_path(index: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for symbol in index.get("symbols", []):
        grouped[symbol["path"]].append(symbol)
    return dict(grouped)

def symbol_list_match_score(symbols: Iterable[dict], chunk: dict, query_tokens: Iterable[str]) -> float:
    score = 0.0
    for symbol in symbols:
        if not (chunk["start"] <= symbol["line"] <= chunk["end"]):
            continue
        name = symbol["name"].lower()
        matches = sum(1 for token in query_tokens if token in name)
        if matches:
            score = max(score, 0.6 + (0.2 * matches))
    return score
def normalize_scores(scored: list[tuple[float, dict]]) -> dict[str, float]:
    if not scored:
        return {}
    values = [score for score, _ in scored]
    high = max(values)
    low = min(values)
    if math.isclose(high, low):
        return {chunk["id"]: 1.0 for _, chunk in scored}
    return {chunk["id"]: (score - low) / (high - low) for score, chunk in scored}
def search_symbols(index: dict, query: str, limit: int) -> list[dict]:
    words = tokenize(query)
    if not words:
        return []
    matches = []
    for symbol in index.get("symbols", []):
        haystack = f"{symbol['name']} {symbol['path']}".lower()
        score = sum(1 for word in words if word in haystack)
        if score:
            matches.append((score, symbol))
    matches.sort(key=lambda item: (-item[0], item[1]["path"], item[1]["line"]))
    return [symbol for _, symbol in matches[:limit]]
def snippet(text: str, query: str, max_chars: int = 360) -> str:
    words = tokenize(query)
    lower = text.lower()
    first = min((lower.find(word) for word in words if lower.find(word) >= 0), default=0)
    start = max(0, first - 100)
    end = min(len(text), start + max_chars)
    value = re.sub(r"\s+", " ", text[start:end]).strip()
    if start:
        value = "..." + value
    if end < len(text):
        value += "..."
    return value
