from __future__ import annotations

import os
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import Iterable

from .config import DEFAULT_EMBED_PROVIDER, OLLAMA_START_TIMEOUT_SECONDS

def embedding_request(
    inputs: list[str],
    model: str,
    dimensions: int | None,
    provider: str = DEFAULT_EMBED_PROVIDER,
) -> list[list[float]]:
    if provider == "ollama":
        return ollama_embedding_request(inputs, model)
    if provider == "openai":
        return openai_embedding_request(inputs, model, dimensions)
    raise SystemExit(f"Unknown embedding provider: {provider}")
def ollama_base_url() -> str:
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
def ollama_is_running() -> bool:
    request = urllib.request.Request(f"{ollama_base_url()}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=2):
            return True
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return False


@contextmanager
def temporary_ollama_server(enabled: bool = True) -> Iterable[None]:
    if not enabled or ollama_is_running():
        yield
        return

    try:
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise SystemExit("Ollama is not installed or not on PATH. Install it, then run `ollama pull nomic-embed-text`.") from exc
    try:
        deadline = time.time() + OLLAMA_START_TIMEOUT_SECONDS
        while time.time() < deadline:
            if ollama_is_running():
                yield
                return
            if process.poll() is not None:
                raise SystemExit("`ollama serve` exited before it became reachable.")
            time.sleep(0.25)
        raise SystemExit("Timed out waiting for `ollama serve` to start.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
def ollama_embedding_request(inputs: list[str], model: str) -> list[list[float]]:
    base_url = ollama_base_url()
    payload = {"model": model, "input": inputs}
    request = urllib.request.Request(
        f"{base_url}/api/embed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Ollama embedding request failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit("Ollama is not reachable. Start it with: ollama serve") from exc

    vectors = body.get("embeddings")
    if len(vectors or []) != len(inputs) or not all(isinstance(vector, list) for vector in vectors or []):
        raise SystemExit("Ollama response did not include one vector per input.")
    return vectors
def openai_embedding_request(inputs: list[str], model: str, dimensions: int | None) -> list[list[float]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required to build or query semantic embeddings.")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload: dict = {"model": model, "input": inputs, "encoding_format": "float"}
    if dimensions:
        payload["dimensions"] = dimensions

    request = urllib.request.Request(
        f"{base_url}/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Embedding API request failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Embedding API request failed: {exc}") from exc

    rows = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
    vectors = [row.get("embedding") for row in rows]
    if len(vectors) != len(inputs) or not all(isinstance(vector, list) for vector in vectors):
        raise SystemExit("Embedding API response did not include one vector per input.")
    return vectors
