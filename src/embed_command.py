from __future__ import annotations

import argparse
import sys
import time

from .config import DEFAULT_EMBED_MODEL, DEFAULT_OPENAI_EMBED_MODEL, EMBEDDINGS_FILE, rel
from .embeddings import (
    batched, chunk_embedding_text, embedding_request, normalize_vector,
    temporary_ollama_server, text_hash,
)
from .indexer import update_index
from .storage import empty_embeddings, load_embeddings, load_index, write_embeddings

def command_embed(args: argparse.Namespace) -> int:
    update_index(full=False)
    index = load_index()
    if args.provider == "openai" and args.model == DEFAULT_EMBED_MODEL:
        args.model = DEFAULT_OPENAI_EMBED_MODEL
    existing = load_embeddings()
    dimensions = None if args.dimensions == 0 else args.dimensions
    if args.provider == "ollama" and dimensions:
        raise SystemExit("Ollama embeddings do not support --dimensions. Use --dimensions 0.")
    if (
        existing.get("provider") != args.provider
        or existing.get("model") != args.model
        or existing.get("dimensions") != dimensions
    ):
        existing = empty_embeddings(args.model, dimensions, args.provider)

    indexed_chunks = {}
    missing = []
    for chunk in index.get("chunks", []):
        source = chunk_embedding_text(chunk)
        source_hash = text_hash(source)
        cached = existing.get("chunks", {}).get(chunk["id"])
        if cached and cached.get("text_sha256") == source_hash:
            if "normalized_embedding" not in cached and isinstance(cached.get("embedding"), list):
                cached["normalized_embedding"] = normalize_vector(cached["embedding"])
            indexed_chunks[chunk["id"]] = cached
            continue
        missing.append({"chunk": chunk, "source": source, "text_sha256": source_hash})

    if missing:
        with temporary_ollama_server(args.provider == "ollama"):
            for group in batched(missing, args.batch_size):
                vectors = embedding_request([item["source"] for item in group], args.model, dimensions, args.provider)
                for item, vector in zip(group, vectors):
                    chunk = item["chunk"]
                    indexed_chunks[chunk["id"]] = {
                        "path": chunk["path"],
                        "start": chunk["start"],
                        "end": chunk["end"],
                        "text_sha256": item["text_sha256"],
                        "embedding": vector,
                        "normalized_embedding": normalize_vector(vector),
                    }
                print(f"Embedded {len(indexed_chunks)}/{len(index.get('chunks', []))} chunks", file=sys.stderr)
    else:
        for chunk_id, cached in list(indexed_chunks.items()):
            if "normalized_embedding" not in cached and isinstance(cached.get("embedding"), list):
                cached["normalized_embedding"] = normalize_vector(cached["embedding"])

    existing["chunks"] = indexed_chunks
    existing["provider"] = args.provider
    existing["model"] = args.model
    existing["dimensions"] = dimensions
    existing["updated_at"] = int(time.time())
    write_embeddings(existing)
    print(
        f"Embedded {len(indexed_chunks)} chunks with {args.provider}:{args.model}"
        f"{f' ({dimensions} dimensions)' if dimensions else ''} -> {rel(EMBEDDINGS_FILE)}"
    )
    return 0
