from __future__ import annotations

import hashlib
import json
import re
import time

from .config import MAX_EMBED_TEXT_CHARS
from .embedding_providers import embedding_request, temporary_ollama_server
from .storage import load_query_embeddings, write_query_embeddings
from .vectors import normalize_vector

def chunk_embedding_text(chunk: dict) -> str:
    prefix = f"{chunk['path']}:{chunk['start']}-{chunk['end']}\n"
    text_budget = max(0, MAX_EMBED_TEXT_CHARS - len(prefix))
    return prefix + chunk["text"][:text_budget]
def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
def normalized_query_text(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())
def embedding_cache_key(provider: str, model: str, dimensions: int | None, query: str) -> str:
    normalized = normalized_query_text(query)
    identity = json.dumps(
        {"provider": provider, "model": model, "dimensions": dimensions, "query": normalized},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()
def query_embedding(
    query: str,
    model: str,
    dimensions: int | None,
    provider: str,
) -> list[float]:
    cache = load_query_embeddings()
    key = embedding_cache_key(provider, model, dimensions, query)
    cached = cache.get("queries", {}).get(key)
    normalized_query = normalized_query_text(query)
    if (
        cached
        and cached.get("provider") == provider
        and cached.get("model") == model
        and cached.get("dimensions") == dimensions
        and cached.get("query") == normalized_query
        and isinstance(cached.get("normalized_embedding"), list)
    ):
        return cached["normalized_embedding"]
    with temporary_ollama_server(provider == "ollama"):
        vector = embedding_request([query], model, dimensions, provider)[0]
    normalized_vector = normalize_vector(vector)
    cache.setdefault("queries", {})[key] = {
        "provider": provider,
        "model": model,
        "dimensions": dimensions,
        "query": normalized_query,
        "normalized_embedding": normalized_vector,
        "created_at": int(time.time()),
    }
    write_query_embeddings(cache)
    return normalized_vector
