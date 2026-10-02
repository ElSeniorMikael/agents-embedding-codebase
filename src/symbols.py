from __future__ import annotations

import ast
import re
from pathlib import Path

TS_SYMBOL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function|class|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
    r"|^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[:=]",
    re.MULTILINE,
)
TS_ROUTE_RE = re.compile(
    r"\b(?:server|app|fastify)\.(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
CSS_SYMBOL_RE = re.compile(r"(?<![A-Za-z0-9_-])([.#][A-Za-z_][A-Za-z0-9_-]*)")
MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
SQL_OBJECT_RE = re.compile(
    r"^\s*(?:create\s+table|alter\s+table|create\s+(?:unique\s+)?index)\s+(?:if\s+not\s+exists\s+)?\"?([A-Za-z_][A-Za-z0-9_]*)\"?",
    re.IGNORECASE | re.MULTILINE,
)

def python_symbols(path: str, text: str) -> list[dict]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    symbols = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                {
                    "path": path,
                    "line": node.lineno,
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "name": node.name,
                }
            )
    return symbols

def generic_symbols(path: str, text: str) -> list[dict]:
    suffix = Path(path).suffix.lower()
    symbols: list[dict] = []
    if suffix in {".js", ".cjs", ".mjs", ".ts", ".tsx"}:
        for match in TS_SYMBOL_RE.finditer(text):
            name = match.group(1) or match.group(2)
            symbols.append({"path": path, "line": text.count("\n", 0, match.start()) + 1, "kind": suffix[1:], "name": name})
        for match in TS_ROUTE_RE.finditer(text):
            method = match.group(1).upper()
            route_path = match.group(2)
            symbols.append(
                {
                    "path": path,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "kind": "route",
                    "name": f"{method} {route_path}",
                }
            )
    elif suffix == ".css":
        seen: set[str] = set()
        for match in CSS_SYMBOL_RE.finditer(text):
            name = match.group(1)
            if name in seen:
                continue
            seen.add(name)
            symbols.append({"path": path, "line": text.count("\n", 0, match.start()) + 1, "kind": "css", "name": name})
    elif suffix == ".md":
        for match in MD_HEADING_RE.finditer(text):
            symbols.append(
                {
                    "path": path,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "kind": f"h{len(match.group(1))}",
                    "name": match.group(2).strip(),
                }
            )
    elif suffix == ".sql":
        for match in SQL_OBJECT_RE.finditer(text):
            symbols.append(
                {
                    "path": path,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "kind": "sql",
                    "name": match.group(1),
                }
            )
    return symbols

def extract_symbols(path: str, text: str) -> list[dict]:
    if Path(path).suffix.lower() == ".py":
        return python_symbols(path, text)
    return generic_symbols(path, text)
