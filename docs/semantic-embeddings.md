# Semantic Embeddings

The default `search` command uses local lexical vectors, which are dependency-free and good for exact project terms.

For meaning-based search, choose one embedding backend.

## Ollama

```bash
ollama pull nomic-embed-text
agent-index embed
```

This creates a cached semantic vector embedding for each indexed chunk. If installed as `.agents`, the cache lives at `.agents/index/embeddings.json`.

The default provider is local Ollama using `nomic-embed-text`, so no OpenAI API key is required. The script starts `ollama serve` automatically when needed and stops the temporary server when it is done. If Ollama is already running, the script reuses it and leaves it running.

## OpenAI

OpenAI is the alternative embedding backend. Use it instead of Ollama by passing `--provider openai`:

```bash
OPENAI_API_KEY=... agent-index embed --provider openai
```

## Cache Behavior

Chunk embeddings store normalized vectors, so semantic and hybrid search can score with dot products instead of recalculating every chunk norm. The raw provider output is still kept for compatibility.

Semantic and hybrid searches also cache query embeddings. If installed as `.agents`, the cache lives at `.agents/index/query_embeddings.json`.

Cache entries are keyed by provider, model, dimensions, and normalized query text, so repeated searches reuse the same query vector without changing ranking results.

Semantic search needs the same provider that built the cache.

If files changed after embeddings were built, semantic and hybrid search reports how many chunk embeddings are missing or stale. Refresh them explicitly:

```bash
agent-index embed
```

For a one-shot refresh plus search, opt in to embedding work:

```bash
agent-index search "how admin ingestion queues worker jobs" --hybrid --auto-embed
```
