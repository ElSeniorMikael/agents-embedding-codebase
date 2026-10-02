# Agent Project Index

Local vector/text indexing for AI agents. Copy this folder into any project so agents can search the codebase without rereading the whole tree every time.

## Install / Setup

Requirements:

- Python 3.10 or newer
- No Python package installs are required for lexical indexing and search
- For vector/semantic search, choose one embedding backend: Ollama with `nomic-embed-text` pulled OR OpenAI with `OPENAI_API_KEY` configured

Copy or clone this repository into the project you want to index. The folder name can be anything, but these examples use `.agents`:

```bash
cd your-project
git clone <your-private-repo-url> .agents
```

The installed folder must include:

- `bin/agent-index`
- `project_index.py`
- `src/`

The script creates `.agents/index/` and the cache files automatically on first run.

Install the global command dispatcher once:

```bash
mkdir -p "$HOME/.local/bin"
cp .agents/bin/agent-index "$HOME/.local/bin/agent-index"
chmod +x "$HOME/.local/bin/agent-index"
```

Make sure `$HOME/.local/bin` is on your `PATH`. After that, use the standard command from anywhere inside the project:

```bash
agent-index search "task topic"
```

Before running vector or hybrid search, set up one embedding backend: Ollama OR OpenAI.

Local Ollama backend:

```bash
ollama pull nomic-embed-text
```

OpenAI backend:

```bash
export OPENAI_API_KEY=...
```

Then build the index and embeddings:

```bash
agent-index update
agent-index embed
agent-index search "task topic" --hybrid
```

If using OpenAI embeddings, pass the provider when embedding:

```bash
agent-index embed --provider openai
```

Lexical-only search does not need Ollama or OpenAI, but it is not vector search:

```bash
agent-index update
agent-index search "task topic"
```

Generated cache files live under `.agents/index/`. Add `.agents/index.config.json` to exclude project-specific generated files or large text files. Set `AGENT_INDEX_ROOT=/path/to/project` only if the folder is not installed directly inside the project root.

Expected installed layout:

```bash
your-project/
  .agents/
    project_index.py
    bin/
      agent-index
    README.md
    src/
```

The folder does not need to be named `.agents`; `.codex`, `.cursor-agent`, or any other project-local agent folder works. The script indexes the parent directory by default and stores generated cache files inside its own `index/` folder.

`project_index.py` remains available as a compatibility entrypoint, but `agent-index` is the preferred command.

## References

- [Commands](docs/commands.md)
- [Agent Workflow](docs/agent-workflow.md)
- [Search Modes](docs/search-modes.md)
- [Semantic Embeddings](docs/semantic-embeddings.md)
- [Indexing](docs/indexing.md)
- [Troubleshooting](docs/troubleshooting.md)
