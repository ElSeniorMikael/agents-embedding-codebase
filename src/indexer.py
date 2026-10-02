from __future__ import annotations

import time
from pathlib import Path

from .chunks import chunk_file_text
from .embeddings import chunk_embedding_text, text_hash
from .fs import FileEntry, all_excludes, file_entry, iter_project_files, read_text
from .storage import empty_index, load_index, rebuild_vectors, write_index
from .symbols import extract_symbols
from .config import INDEX_FILE, rel

def index_file(path: Path, entry: FileEntry) -> tuple[list[dict], list[dict]]:
    text = read_text(path)
    if text is None:
        return [], []
    return chunk_file_text(entry.path, text), extract_symbols(entry.path, text)

def update_index(full: bool = False) -> dict:
    excludes = all_excludes()
    existing = empty_index() if full else load_index()
    current_entries: dict[str, FileEntry] = {}
    changed: list[tuple[Path, FileEntry]] = []

    for path in iter_project_files(excludes):
        entry = file_entry(path)
        if entry is None:
            continue
        current_entries[entry.path] = entry
        old = existing["files"].get(entry.path)
        if old is None or old.get("sha256") != entry.sha256:
            changed.append((path, entry))

    removed = set(existing["files"]) - set(current_entries)
    if removed or changed:
        changed_paths = {entry.path for _, entry in changed}
        drop_paths = removed | changed_paths
        existing["chunks"] = [chunk for chunk in existing["chunks"] if chunk["path"] not in drop_paths]
        existing["symbols"] = [symbol for symbol in existing["symbols"] if symbol["path"] not in drop_paths]

        for path, entry in changed:
            chunks, symbols = index_file(path, entry)
            existing["chunks"].extend(chunks)
            existing["symbols"].extend(symbols)

    existing["files"] = {path: entry.__dict__ for path, entry in sorted(current_entries.items())}
    existing["updated_at"] = int(time.time())
    rebuild_vectors(existing)
    write_index(existing)
    return {
        "files": len(existing["files"]),
        "chunks": len(existing["chunks"]),
        "symbols": len(existing["symbols"]),
        "changed": len(changed),
        "removed": len(removed),
        "index": rel(INDEX_FILE),
    }

def embedding_freshness(index: dict, embeddings: dict) -> dict:
    chunk_vectors = embeddings.get("chunks", {})
    missing = 0
    stale = 0
    current = 0
    for chunk in index.get("chunks", []):
        current += 1
        source_hash = text_hash(chunk_embedding_text(chunk))
        cached = chunk_vectors.get(chunk["id"])
        if not cached:
            missing += 1
        elif cached.get("text_sha256") != source_hash:
            stale += 1
    extra = max(0, len(chunk_vectors) - current)
    return {"missing": missing, "stale": stale, "extra": extra, "total": current}
