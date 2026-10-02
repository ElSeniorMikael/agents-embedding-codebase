from __future__ import annotations

import argparse

from .config import (
    DEFAULT_EMBED_DIMENSIONS, DEFAULT_EMBED_MODEL, DEFAULT_EMBED_PROVIDER,
    EMBED_BATCH_SIZE, command_hint,
)
from .embeddings import dot, normalize_vector, query_embedding
from .indexer import embedding_freshness
from .storage import load_embeddings

def ensure_embeddings_ready(
    index: dict,
    embeddings: dict,
    auto_embed: bool,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    chunk_vectors = embeddings.get("chunks", {})
    if not chunk_vectors:
        if auto_embed:
            from .embed_command import command_embed

            command_embed(
                argparse.Namespace(
                    provider=provider or DEFAULT_EMBED_PROVIDER,
                    model=model or DEFAULT_EMBED_MODEL,
                    dimensions=DEFAULT_EMBED_DIMENSIONS,
                    batch_size=EMBED_BATCH_SIZE,
                )
            )
            return load_embeddings()
        raise SystemExit(f"No semantic embeddings found. Run: {command_hint('embed')}")

    freshness = embedding_freshness(index, embeddings)
    if freshness["missing"] or freshness["stale"]:
        if auto_embed:
            from .embed_command import command_embed

            command_embed(
                argparse.Namespace(
                    provider=provider or embeddings.get("provider") or DEFAULT_EMBED_PROVIDER,
                    model=model or embeddings.get("model") or DEFAULT_EMBED_MODEL,
                    dimensions=embeddings.get("dimensions") or DEFAULT_EMBED_DIMENSIONS,
                    batch_size=EMBED_BATCH_SIZE,
                )
            )
            return load_embeddings()
        raise SystemExit(
            "Semantic embeddings are stale "
            f"({freshness['missing']} missing, {freshness['stale']} stale of {freshness['total']} chunks). "
            f"Refresh with: {command_hint('embed')} "
            "or search with --auto-embed to refresh explicitly."
        )
    return embeddings
def score_semantic_chunks(
    index: dict,
    query: str,
    limit: int,
    model: str | None = None,
    provider: str | None = None,
    auto_embed: bool = False,
) -> list[tuple[float, dict]]:
    embeddings = load_embeddings()
    embeddings = ensure_embeddings_ready(index, embeddings, auto_embed, provider, model)
    chunk_vectors = embeddings.get("chunks", {})

    cached_model = embeddings.get("model") or DEFAULT_EMBED_MODEL
    cached_provider = embeddings.get("provider") or DEFAULT_EMBED_PROVIDER
    if model and model != cached_model:
        raise SystemExit(
            f"Cached embeddings use {cached_model}. Rebuild with: {command_hint(f'embed --model {model}')}"
        )
    if provider and provider != cached_provider:
        raise SystemExit(
            f"Cached embeddings use {cached_provider}. "
            f"Rebuild with: {command_hint(f'embed --provider {provider}')}"
        )
    embed_model = cached_model
    embed_provider = cached_provider
    dimensions = embeddings.get("dimensions")
    query_vector = query_embedding(query, embed_model, dimensions, embed_provider)
    chunks_by_id = {chunk["id"]: chunk for chunk in index.get("chunks", [])}

    scored = []
    for chunk_id, entry in chunk_vectors.items():
        chunk = chunks_by_id.get(chunk_id)
        vector = entry.get("normalized_embedding") or entry.get("embedding")
        if not chunk or not isinstance(vector, list):
            continue
        if "normalized_embedding" not in entry:
            vector = normalize_vector(vector)
        scored.append((dot(query_vector, vector), chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:limit]
