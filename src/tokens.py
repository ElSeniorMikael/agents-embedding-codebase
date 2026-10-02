from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")

def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for raw in TOKEN_RE.findall(text.lower()):
        if raw.isdigit() or len(raw) > 48:
            continue
        tokens.append(raw)
    return tokens
