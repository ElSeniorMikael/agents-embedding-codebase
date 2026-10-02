from __future__ import annotations

import time
from pathlib import Path

from .chunks import chunk_file_text
from .config import INDEX_FILE, rel
from .embeddings import chunk_embedding_text, text_hash
from .fs import FileEntry, all_excludes, iter_project_files, read_file_entry
from .storage import empty_index, load_index, rebuild_vectors, write_index
from .symbols import extract_symbols

def index_file(entry: FileEntry, text: str) -> tuple[list[dict], list[dict]]:
    return chunk_file_text(entry.path, text), extract_symbols(entry.path, text)

def unchanged_entry(path: Path, old: dict | None) -> FileEntry | None:
    if not old:
        return None
    try:
        stat = path.stat()
    except OSError:
        return None
    if old.get("size") != stat.st_size or old.get("mtime_ns") != stat.st_mtime_ns:
        return None
    old_path = old.get("path")
    old_sha = old.get("sha256")
    if not isinstance(old_path, str) or not isinstance(old_sha, str):
        return None
    if old_path != rel(path):
        return None
    return FileEntry(path=old_path, sha256=old_sha, size=stat.st_size, mtime_ns=stat.st_mtime_ns)

def update_index(full: bool = False) -> dict:
    excludes = all_excludes()
    existing = empty_index() if full else load_index()
    current_entries: dict[str, FileEntry] = {}
    changed: list[tuple[FileEntry, str]] = []

    for path in iter_project_files(excludes):
        path_rel = rel(path)
        old = existing["files"].get(path_rel)
        entry = None if full else unchanged_entry(path, old)
        if entry is not None:
            current_entries[entry.path] = entry
            continue

        current = read_file_entry(path)
        if current is None:
            continue
        entry, text = current
        current_entries[entry.path] = entry
        if old is None or old.get("sha256") != entry.sha256:
            changed.append((entry, text))

    removed = set(existing["files"]) - set(current_entries)
    if removed or changed:
        changed_paths = {entry.path for entry, _ in changed}
        drop_paths = removed | changed_paths
        existing["chunks"] = [chunk for chunk in existing["chunks"] if chunk["path"] not in drop_paths]
        existing["symbols"] = [symbol for symbol in existing["symbols"] if symbol["path"] not in drop_paths]

        for entry, text in changed:
            chunks, symbols = index_file(entry, text)
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
    current_ids = set()
    missing = 0
    stale = 0
    current = 0
    for chunk in index.get("chunks", []):
        current += 1
        current_ids.add(chunk["id"])
        source_hash = text_hash(chunk_embedding_text(chunk))
        cached = chunk_vectors.get(chunk["id"])
        if not cached:
            missing += 1
        elif cached.get("text_sha256") != source_hash:
            stale += 1
    extra = len(set(chunk_vectors) - current_ids)
    return {"missing": missing, "stale": stale, "extra": extra, "total": current}
