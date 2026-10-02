from __future__ import annotations

import hashlib
from collections import Counter

from .config import CHUNK_LINES, CHUNK_OVERLAP
from .tokens import tokenize

def split_chunks(path: str, text: str) -> list[dict]:
    lines = text.splitlines()
    if not lines:
        return []
    chunks = []
    step = max(1, CHUNK_LINES - CHUNK_OVERLAP)
    for start in range(0, len(lines), step):
        chunk_lines = lines[start : start + CHUNK_LINES]
        if not chunk_lines:
            break
        chunk_text = "\n".join(chunk_lines).strip()
        if not chunk_text:
            continue
        chunk_id = hashlib.sha1(f"{path}:{start + 1}:{chunk_text[:80]}".encode("utf-8")).hexdigest()[:16]
        chunks.append(
            {
                "id": chunk_id,
                "path": path,
                "start": start + 1,
                "end": start + len(chunk_lines),
                "text": chunk_text,
                "tokens": dict(Counter(tokenize(chunk_text))),
            }
        )
    return chunks
def make_chunk(path: str, lines: list[str], start: int, end: int, kind: str = "lines") -> dict | None:
    chunk_lines = lines[start - 1 : end]
    chunk_text = "\n".join(chunk_lines).strip()
    if not chunk_text:
        return None
    chunk_id = hashlib.sha1(f"{path}:{start}:{kind}:{chunk_text[:80]}".encode("utf-8")).hexdigest()[:16]
    return {
        "id": chunk_id,
        "path": path,
        "start": start,
        "end": end,
        "kind": kind,
        "text": chunk_text,
        "tokens": dict(Counter(tokenize(chunk_text))),
    }
def bounded_chunks(path: str, lines: list[str], start: int, end: int, kind: str) -> list[dict]:
    chunks = []
    current = start
    while current <= end:
        chunk_end = min(end, current + CHUNK_LINES - 1)
        chunk = make_chunk(path, lines, current, chunk_end, kind)
        if chunk:
            chunks.append(chunk)
        current = chunk_end + 1
    return chunks
