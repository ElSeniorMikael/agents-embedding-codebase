from __future__ import annotations

import json
from collections import Counter

from .config import (
    DEFAULT_EMBED_MODEL, DEFAULT_EMBED_PROVIDER, EMBEDDINGS_FILE,
    EMBEDDINGS_VERSION, INDEX_DIR, INDEX_FILE, QUERY_EMBEDDINGS_FILE,
    QUERY_EMBEDDINGS_VERSION, ROOT, VERSION,
)

def ensure_index_files() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    for path in (INDEX_FILE, EMBEDDINGS_FILE, QUERY_EMBEDDINGS_FILE):
        path.touch(exist_ok=True)

def empty_index() -> dict:
    return {
        "version": VERSION,
        "root": str(ROOT),
        "updated_at": None,
        "files": {},
        "chunks": [],
        "symbols": [],
        "doc_freq": {},
        "chunk_count": 0,
    }

def load_index() -> dict:
    ensure_index_files()
    if not INDEX_FILE.exists():
        return empty_index()
    try:
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return empty_index()
    if index.get("version") != VERSION or index.get("root") != str(ROOT):
        return empty_index()
    return index

def write_index(index: dict) -> None:
    ensure_index_files()
    tmp_path = INDEX_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(INDEX_FILE)

def load_embeddings() -> dict:
    ensure_index_files()
    if not EMBEDDINGS_FILE.exists():
        return empty_embeddings()
    try:
        data = json.loads(EMBEDDINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return empty_embeddings()
    if data.get("version") != EMBEDDINGS_VERSION or data.get("root") != str(ROOT):
        return empty_embeddings()
    return data

def empty_embeddings(
    model: str = DEFAULT_EMBED_MODEL,
    dimensions: int | None = None,
    provider: str = DEFAULT_EMBED_PROVIDER,
) -> dict:
    return {
        "version": EMBEDDINGS_VERSION,
        "root": str(ROOT),
        "provider": provider,
        "model": model,
        "dimensions": dimensions,
        "updated_at": None,
        "chunks": {},
    }

def write_embeddings(data: dict) -> None:
    ensure_index_files()
    tmp_path = EMBEDDINGS_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(data, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(EMBEDDINGS_FILE)

def empty_query_embeddings() -> dict:
    return {
        "version": QUERY_EMBEDDINGS_VERSION,
        "root": str(ROOT),
        "queries": {},
    }

def load_query_embeddings() -> dict:
    ensure_index_files()
    if not QUERY_EMBEDDINGS_FILE.exists():
        return empty_query_embeddings()
    try:
        data = json.loads(QUERY_EMBEDDINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return empty_query_embeddings()
    if data.get("version") != QUERY_EMBEDDINGS_VERSION or data.get("root") != str(ROOT):
        return empty_query_embeddings()
    if not isinstance(data.get("queries"), dict):
        data["queries"] = {}
    return data

def write_query_embeddings(data: dict) -> None:
    ensure_index_files()
    tmp_path = QUERY_EMBEDDINGS_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(data, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(QUERY_EMBEDDINGS_FILE)

def rebuild_vectors(index: dict) -> None:
    doc_freq: Counter[str] = Counter()
    for chunk in index["chunks"]:
        doc_freq.update(chunk.get("tokens", {}).keys())
    index["doc_freq"] = dict(doc_freq)
    index["chunk_count"] = len(index["chunks"])
