from __future__ import annotations

from .config import HYBRID_CANDIDATE_MULTIPLIER
from .lexical_search import score_chunks
from .search_utils import normalize_scores, path_name_score, symbol_match_score
from .semantic_search import score_semantic_chunks
from .tokens import tokenize

def score_hybrid_chunks(
    index: dict,
    query: str,
    limit: int,
    lexical_weight: float,
    semantic_weight: float,
    model: str | None = None,
    provider: str | None = None,
    auto_embed: bool = False,
) -> list[tuple[float, dict]]:
    candidate_limit = max(limit, limit * HYBRID_CANDIDATE_MULTIPLIER)
    lexical = score_chunks(index, query, candidate_limit)
    semantic = score_semantic_chunks(index, query, candidate_limit, model, provider, auto_embed)
    lexical_scores = normalize_scores(lexical)
    semantic_scores = normalize_scores(semantic)
    chunks = {chunk["id"]: chunk for _, chunk in [*lexical, *semantic]}
    query_tokens = tokenize(query)
    fused: list[tuple[float, dict]] = []
    for chunk_id, chunk in chunks.items():
        lexical_part = lexical_scores.get(chunk_id, 0.0)
        semantic_part = semantic_scores.get(chunk_id, 0.0)
        name_part = path_name_score(chunk, query_tokens)
        symbol_part = symbol_match_score(index, chunk, query_tokens)
        score = (lexical_part * lexical_weight) + (semantic_part * semantic_weight) + name_part + symbol_part
        if lexical_part >= 0.92:
            score += 0.35
        fused.append((score, chunk))
    fused.sort(key=lambda item: (item[0], path_name_score(item[1], query_tokens)), reverse=True)
    return fused[:limit]
