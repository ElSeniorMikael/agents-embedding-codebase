# Troubleshooting

## `agent-index: command not found`

The global dispatcher is not installed or its install folder is not on `PATH`.

Install it:

```bash
mkdir -p "$HOME/.local/bin"
cp .agents/bin/agent-index "$HOME/.local/bin/agent-index"
chmod +x "$HOME/.local/bin/agent-index"
```

Check whether `$HOME/.local/bin` is on `PATH`:

```bash
echo "$PATH"
```

If missing, add it to your shell profile:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then restart the shell or source the profile file.

## `agent-index: no project index found`

Run the command from inside a project that has this tool installed as one of:

- `.agents`
- `.codex`
- `.cursor-agent`
- `.agent-index`

Expected layout:

```bash
your-project/
  .agents/
    project_index.py
    src/
    bin/
      agent-index
```

If you use another folder name, configure the dispatcher:

```bash
export AGENT_INDEX_DIR_NAMES=".my-agent-folder:.agents:.codex"
```

## `No semantic embeddings found`

Build embeddings before semantic or hybrid search:

```bash
agent-index embed
```

If using OpenAI:

```bash
agent-index embed --provider openai
```

## `Ollama is not installed or not on PATH`

Install Ollama and pull the text embedding model:

```bash
ollama pull nomic-embed-text
```

Then rerun:

```bash
agent-index embed
```

## `OPENAI_API_KEY is required`

Set the key before using the OpenAI provider:

```bash
export OPENAI_API_KEY=...
agent-index embed --provider openai
```

## Semantic embeddings are stale

Files changed after embeddings were built. Refresh embeddings:

```bash
agent-index embed
```

Or allow a search to refresh explicitly:

```bash
agent-index search "task topic" --hybrid --auto-embed
```

## Wrong project is being indexed

By default, the installed agent folder indexes its parent directory. If the folder is not installed directly under the target project, set:

```bash
export AGENT_INDEX_ROOT=/path/to/project
```
