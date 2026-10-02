from __future__ import annotations

import math
from collections import Counter

from .tokens import tokenize

def score_chunks(index: dict, query: str, limit: int) -> list[tuple[float, dict]]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
    query_counts = Counter(query_tokens)
    chunk_count = max(1, index.get("chunk_count", 0))
    doc_freq = index.get("doc_freq", {})
    scored = []
    for chunk in index.get("chunks", []):
        terms = chunk.get("tokens", {})
        score = 0.0
        for token, query_tf in query_counts.items():
            tf = terms.get(token, 0)
            if not tf:
                continue
            idf = math.log((chunk_count + 1) / (doc_freq.get(token, 0) + 1)) + 1
            score += (1 + math.log(tf)) * idf * query_tf
        if score:
            path_boost = sum(0.35 for token in query_counts if token in chunk["path"].lower())
            scored.append((score + path_boost, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:limit]
