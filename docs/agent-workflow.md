# Agent Workflow

Agents should refresh and read the local project index before scoping implementation work:

```bash
agent-index update
agent-index search "task topic" --hybrid
```

Use the returned files, symbols, and line ranges as the starting map, then open the relevant source and documentation files before editing.

If hybrid or semantic search reports missing or stale embeddings, refresh them explicitly:

```bash
agent-index embed
agent-index search "task topic" --hybrid
```

This keeps agent chats aligned around the same local RAG context and avoids repeatedly rereading the full repository.

## Search Policy

Agents should choose the search mode based on the shape of the task:

- Use lexical search when the task includes exact project words, file names, function names, API paths, symbols, or error messages.
- Use semantic search when the task is broad or fuzzy and the exact local names are unknown.
- Use hybrid search as the default investigation mode after embeddings are built, because it combines exact project matches with meaning-based matches.

Default agent flow after setup:

```bash
agent-index update
agent-index search "task topic" --hybrid
```

If no embedding backend is available yet, fall back to lexical search:

```bash
agent-index search "task topic"
```

Agents should treat search results as a map, not as a substitute for reading source files. After search, open the relevant files and inspect the returned line ranges before editing.
