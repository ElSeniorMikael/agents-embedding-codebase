from __future__ import annotations

import os
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "project_index.py"
AGENT_DIR = SCRIPT_PATH.parent
ROOT = Path(os.environ.get("AGENT_INDEX_ROOT", AGENT_DIR.parent)).resolve()
INDEX_DIR = AGENT_DIR / "index"
INDEX_FILE = INDEX_DIR / "index.json"
EMBEDDINGS_FILE = INDEX_DIR / "embeddings.json"
QUERY_EMBEDDINGS_FILE = INDEX_DIR / "query_embeddings.json"

VERSION = 1
EMBEDDINGS_VERSION = 1
QUERY_EMBEDDINGS_VERSION = 1
MAX_QUERY_EMBEDDINGS = 500
DEFAULT_EMBED_PROVIDER = "ollama"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_OPENAI_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_EMBED_DIMENSIONS = 0
EMBED_BATCH_SIZE = 32
OLLAMA_START_TIMEOUT_SECONDS = 30
MAX_EMBED_TEXT_CHARS = 3500
MAX_FILE_BYTES = 512 * 1024
CHUNK_LINES = 120
CHUNK_OVERLAP = 20
MIN_CODE_CHUNK_LINES = 16
HYBRID_CANDIDATE_MULTIPLIER = 4
DEFAULT_LEXICAL_WEIGHT = 0.55
DEFAULT_SEMANTIC_WEIGHT = 0.45

DEFAULT_EXCLUDES = (
    ".git/**",
    "node_modules/**",
    ".venv/**",
    ".venv-*",
    ".venv-*/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "*.pyc",
    "*.pyo",
    "*.tsbuildinfo",
    "*.d.ts",
    "*.icns",
    "*.ico",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.webp",
    "*.mp4",
    "*.webm",
    "*.zip",
    "*.pkg",
    "*.pyz",
    "*.toc",
    ".DS_Store",
)

TEXT_EXTENSIONS = {
    ".css", ".html", ".js", ".json", ".md", ".ps1", ".py",
    ".cjs", ".mjs", ".sh", ".spec", ".sql", ".ts", ".tsx",
    ".toml", ".txt", ".yml", ".yaml",
}

def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return os.path.relpath(path, ROOT)

def rel_agent(path: Path) -> str:
    try:
        return path.relative_to(AGENT_DIR).as_posix()
    except ValueError:
        return os.path.relpath(path, AGENT_DIR)

def command_hint(command: str) -> str:
    return f"agent-index {command}"
