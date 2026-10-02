from __future__ import annotations

import argparse
import time

from .config import AGENT_DIR, EMBEDDINGS_FILE, INDEX_FILE, QUERY_EMBEDDINGS_FILE, ROOT, command_hint, rel
from .embed_command import command_embed
from .indexer import embedding_freshness, update_index
from .search import score_chunks, score_hybrid_chunks, score_semantic_chunks, search_symbols, snippet
from .storage import load_embeddings, load_index, load_query_embeddings

def command_update(args: argparse.Namespace) -> int:
    stats = update_index(full=args.full)
    print(
        f"Indexed {stats['files']} files, {stats['chunks']} chunks, {stats['symbols']} symbols "
        f"({stats['changed']} changed, {stats['removed']} removed) -> {stats['index']}"
    )
    return 0
def command_status(_: argparse.Namespace) -> int:
    index = load_index()
    embeddings = load_embeddings()
    query_embeddings = load_query_embeddings()
    freshness = embedding_freshness(index, embeddings) if embeddings.get("chunks") else None
    updated_at = index.get("updated_at")
    embedded_at = embeddings.get("updated_at")
    updated = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(updated_at)) if updated_at else "never"
    embedded = time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(embedded_at)) if embedded_at else "never"
    print(f"Project root: {ROOT}")
    print(f"Agent folder: {rel(AGENT_DIR)}")
    print(f"Index: {rel(INDEX_FILE)}")
    print(f"Updated: {updated}")
    print(f"Files: {len(index.get('files', {}))}")
    print(f"Chunks: {len(index.get('chunks', []))}")
    print(f"Symbols: {len(index.get('symbols', []))}")
    print(f"Embeddings: {rel(EMBEDDINGS_FILE)}")
    print(f"Embedded: {embedded}")
    print(f"Embedded chunks: {len(embeddings.get('chunks', {}))}")
    print(f"Embedding provider: {embeddings.get('provider')}")
    print(f"Embedding model: {embeddings.get('model')}")
    print(f"Embedding dimensions: {embeddings.get('dimensions')}")
    if freshness:
        print(f"Embedding freshness: {freshness['missing']} missing, {freshness['stale']} stale, {freshness['extra']} extra")
    print(f"Query embedding cache: {rel(QUERY_EMBEDDINGS_FILE)}")
    print(f"Cached queries: {len(query_embeddings.get('queries', {}))}")
    return 0
def command_search(args: argparse.Namespace) -> int:
    index = load_index()
    if not index.get("chunks"):
        print(f"No index found. Run: {command_hint('update')}")
        return 1
    symbol_matches = search_symbols(index, args.query, min(args.limit, 8))
    chunk_matches = score_chunks(index, args.query, args.limit)

    if symbol_matches:
        print("Symbols")
        for symbol in symbol_matches:
            print(f"  {symbol['path']}:{symbol['line']} [{symbol['kind']}] {symbol['name']}")
        print()

    mode = "hybrid" if args.hybrid else "semantic" if args.semantic else "lexical"
    print("Chunks" + (f" ({mode})" if mode != "lexical" else ""))
    if args.hybrid:
        matches = score_hybrid_chunks(
            index,
            args.query,
            args.limit,
            args.lexical_weight,
            args.semantic_weight,
            args.model,
            args.provider,
            args.auto_embed,
        )
    elif args.semantic:
        matches = score_semantic_chunks(index, args.query, args.limit, args.model, args.provider, args.auto_embed)
    else:
        matches = chunk_matches
    if not matches:
        print("  No matches.")
        return 0
    for score, chunk in matches:
        print(f"  {chunk['path']}:{chunk['start']}-{chunk['end']} score={score:.2f}")
        print(f"    {snippet(chunk['text'], args.query)}")
    return 0
