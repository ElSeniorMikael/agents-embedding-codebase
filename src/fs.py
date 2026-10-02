from __future__ import annotations

import fnmatch
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import AGENT_DIR, DEFAULT_EXCLUDES, MAX_FILE_BYTES, ROOT, TEXT_EXTENSIONS, rel, rel_agent

@dataclass(frozen=True)
class FileEntry:
    path: str
    sha256: str
    size: int
    mtime_ns: int

def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)

def load_extra_excludes() -> list[str]:
    config_path = AGENT_DIR / "index.config.json"
    if not config_path.exists():
        return []
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid {rel_agent(config_path)}: {exc}") from exc
    excludes = data.get("exclude", [])
    if not isinstance(excludes, list) or not all(isinstance(item, str) for item in excludes):
        raise SystemExit(f"{rel_agent(config_path)} must contain an optional string list named 'exclude'")
    return excludes

def all_excludes() -> tuple[str, ...]:
    agent_dir = rel(AGENT_DIR)
    return (*DEFAULT_EXCLUDES, f"{agent_dir}/**", agent_dir, *load_extra_excludes())

def is_text_candidate(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    return path.name in {"LICENSE", "Makefile", "Dockerfile"}

def iter_project_files(excludes: tuple[str, ...]) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(ROOT):
        root_path = Path(current_root)
        kept_dirs = []
        for dirname in dirnames:
            dir_rel = rel(root_path / dirname)
            if not matches_any(f"{dir_rel}/**", excludes) and not matches_any(dir_rel, excludes):
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            path = root_path / filename
            path_rel = rel(path)
            if matches_any(path_rel, excludes):
                continue
            if not is_text_candidate(path):
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path

def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            return None

def file_entry(path: Path) -> FileEntry | None:
    text = read_text(path)
    if text is None:
        return None
    stat = path.stat()
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return FileEntry(path=rel(path), sha256=digest, size=stat.st_size, mtime_ns=stat.st_mtime_ns)
