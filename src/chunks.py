from __future__ import annotations

from pathlib import Path

from .chunk_utils import bounded_chunks, make_chunk, split_chunks
from .code_chunks import python_code_chunks, typescript_code_chunks

def chunk_file_text(path: str, text: str) -> list[dict]:
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        chunks = python_code_chunks(path, text)
        if chunks:
            return chunks
    if suffix in {".js", ".cjs", ".mjs", ".ts", ".tsx"}:
        chunks = typescript_code_chunks(path, text)
        if chunks:
            return chunks
    return split_chunks(path, text)
