"""Prepare the default embedding model without building a project index."""

from __future__ import annotations

import subprocess

from .config import DEFAULT_EMBED_MODEL
from .embedding_providers import temporary_ollama_server


def main() -> int:
    with temporary_ollama_server():
        result = subprocess.run(["ollama", "pull", DEFAULT_EMBED_MODEL], check=False)
        if result.returncode:
            raise SystemExit("Ollama model download failed; retry with: ollama pull " + DEFAULT_EMBED_MODEL)
    print(f"Ollama is ready with {DEFAULT_EMBED_MODEL}. Run the project's embed command next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
