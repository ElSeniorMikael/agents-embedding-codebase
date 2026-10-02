from __future__ import annotations

import ast
import re

from .config import CHUNK_LINES, MIN_CODE_CHUNK_LINES
from .chunk_utils import bounded_chunks, make_chunk

TS_SYMBOL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
    r"|^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[:=]",
    re.MULTILINE,
)

def python_code_chunks(path: str, text: str) -> list[dict]:
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    spans: list[tuple[int, int]] = []
    for node in tree.body:
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = int(getattr(node, "lineno", 1))
        end = int(getattr(node, "end_lineno", start))
        if end >= start:
            spans.append((start, end))
    if not spans:
        return []

    chunks: list[dict] = []
    pending_start: int | None = None
    pending_end: int | None = None
    for start, end in spans:
        span_length = end - start + 1
        if span_length >= MIN_CODE_CHUNK_LINES:
            if pending_start is not None and pending_end is not None:
                chunks.extend(bounded_chunks(path, lines, pending_start, pending_end, "python-symbol-group"))
                pending_start = pending_end = None
            chunks.extend(bounded_chunks(path, lines, start, end, "python-symbol"))
            continue
        if pending_start is None:
            pending_start = start
            pending_end = end
        elif end - pending_start + 1 <= CHUNK_LINES:
            pending_end = end
        else:
            chunks.extend(bounded_chunks(path, lines, pending_start, pending_end or start, "python-symbol-group"))
            pending_start = start
            pending_end = end
    if pending_start is not None and pending_end is not None:
        chunks.extend(bounded_chunks(path, lines, pending_start, pending_end, "python-symbol-group"))

    covered = [(chunk["start"], chunk["end"]) for chunk in chunks]
    prologue_end = min(start for start, _ in spans) - 1
    if prologue_end > 0:
        prologue = make_chunk(path, lines, 1, prologue_end, "python-module")
        if prologue:
            chunks.insert(0, prologue)

    gaps: list[tuple[int, int]] = []
    previous_end = prologue_end
    for start, end in sorted(covered):
        if start - previous_end > MIN_CODE_CHUNK_LINES:
            gaps.append((previous_end + 1, start - 1))
        previous_end = max(previous_end, end)
    if len(lines) - previous_end >= MIN_CODE_CHUNK_LINES:
        gaps.append((previous_end + 1, len(lines)))
    for start, end in gaps:
        chunks.extend(bounded_chunks(path, lines, start, end, "python-context"))
    return sorted(chunks, key=lambda chunk: (chunk["start"], chunk["end"]))
def typescript_code_chunks(path: str, text: str) -> list[dict]:
    lines = text.splitlines()
    spans: list[tuple[int, int]] = []
    for match in TS_SYMBOL_RE.finditer(text):
        start = text.count("\n", 0, match.start()) + 1
        next_match = TS_SYMBOL_RE.search(text, match.end())
        next_start = text.count("\n", 0, next_match.start()) + 1 if next_match else len(lines) + 1
        end = min(len(lines), max(start, next_start - 1))
        if end >= start:
            spans.append((start, end))
    if not spans:
        return []

    chunks: list[dict] = []
    for start, end in spans:
        chunks.extend(bounded_chunks(path, lines, start, end, "ts-symbol"))

    first_start = min(start for start, _ in spans)
    if first_start > 1:
        prologue = make_chunk(path, lines, 1, first_start - 1, "ts-module")
        if prologue:
            chunks.insert(0, prologue)
    return sorted(chunks, key=lambda chunk: (chunk["start"], chunk["end"]))
