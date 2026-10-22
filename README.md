# Agent Project Index

Local vector/text indexing for AI agents. Copy this folder into any project so agents can search the codebase without rereading the whole tree every time.

## Install / Setup

Requirements:

- Python 3.10 or newer
- No Python package installs are required for lexical indexing and search
- For vector/semantic search, choose one embedding backend: Ollama with `nomic-embed-text` pulled OR OpenAI with `OPENAI_API_KEY` configured

Copy or clone this repository into the project you want to index. The folder name can be anything, but these examples use `.agents/embedding-codebase`:

Install only the runtime files with the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | sh
```

By default this installs into `.agents/embedding-codebase/` in the current directory. To choose another folder:

```bash
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | AGENT_INDEX_INSTALL_DIR=.codex sh
```

To also install the global dispatcher into `$HOME/.local/bin`:

```bash
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | AGENT_INDEX_INSTALL_GLOBAL=1 sh
```

Alternatively, copy or clone the full repository:

```bash
cd your-project
git clone <your-private-repo-url> .agents/embedding-codebase
```

The installed folder must include:

- `bin/agent-index`
- `project_index.py`
- `src/`

The script creates `.agents/embedding-codebase/index/` and the cache files automatically on first run.

Install the global command dispatcher once:

```bash
mkdir -p "$HOME/.local/bin"
cp .agents/embedding-codebase/bin/agent-index "$HOME/.local/bin/agent-index"
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

Generated cache files live under `.agents/embedding-codebase/index/`. Add `.agents/embedding-codebase/index.config.json` to exclude project-specific generated files or large text files. The default nested layout indexes the project containing `.agents`. Set `AGENT_INDEX_ROOT=/path/to/project` to override the detected project root.

Expected installed layout:

```bash
your-project/
  .agents/
    embedding-codebase/
      project_index.py
      bin/
        agent-index
      README.md
      src/
```

The runtime keeps its files and cache inside `.agents/embedding-codebase/`, alongside any other tools in `.agents/`. Existing direct installations in `.agents`, `.codex`, `.cursor-agent`, or `.agent-index` still work and index their parent directory. For a custom installation path, set `AGENT_INDEX_DIR_NAMES` to that project-relative path so the dispatcher can find it. A runtime directly inside `.agents/` indexes the project containing `.agents`; other layouts index the runtime's parent unless `AGENT_INDEX_ROOT` is set.

If you already installed the global dispatcher, repeat the dispatcher installation command above so it recognizes the new nested layout.

`project_index.py` remains available as a compatibility entrypoint, but `agent-index` is the preferred command.

## Agent startup rule

Add the following rule to your project's `AGENTS.md` or your agent's equivalent project rules file so the index stays current across tasks and chats:

```text
At the start of every new task or chat, run `agent-index update` from inside
the project before searching the index or scoping implementation work.
Use the refreshed index to find relevant files, then read those files before editing.
If semantic or hybrid search reports missing or stale embeddings, run
`agent-index embed` with the configured provider before retrying the search.
```

`agent-index update` is incremental, so unchanged files do not need to be rechunked. See [Agent Workflow](docs/agent-workflow.md) for search guidance.

## References

- [Commands](docs/commands.md)
- [Agent Workflow](docs/agent-workflow.md)
- [Search Modes](docs/search-modes.md)
- [Semantic Embeddings](docs/semantic-embeddings.md)
- [Indexing](docs/indexing.md)
- [Troubleshooting](docs/troubleshooting.md)
