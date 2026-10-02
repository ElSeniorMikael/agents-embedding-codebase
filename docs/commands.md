# Commands

Run these from anywhere inside a project that has the agent index folder installed.

```bash
agent-index build
agent-index update
agent-index status
agent-index search "admin settings route"
agent-index embed
agent-index search "where archive ingestion jobs are handled" --semantic
agent-index search "where archive ingestion jobs are handled" --hybrid
```

`build` recreates the index from scratch. `update` is incremental: it checks file hashes, removes deleted files, and only rechunks changed files.

Commands that build or use vector embeddings require one backend: Ollama with `nomic-embed-text` available OR OpenAI with `OPENAI_API_KEY` configured.

Generated index data lives in the installed agent folder's `index/` directory. If you install as `.agents`, that path is `.agents/index/`.
