# Search Modes

Lexical search is the default:

```bash
agent-index search "catalog correction service"
```

Use it when the query has exact project terms, file names, function names, API paths, or error messages.

Semantic search ranks chunks by meaning with cached embeddings:

```bash
agent-index search "where API errors are logged" --semantic
```

Use it for broad or fuzzy questions when you may not know the exact local names.

Hybrid search fuses lexical and semantic candidates:

```bash
agent-index search "catalog correction service" --hybrid
```

Use it as the default broad-scoping mode when exact project words matter but surrounding meaning should also influence the result. Hybrid ranking favors exact token, path, filename, and symbol matches while still considering semantic similarity.

The default weights are balanced for code search, and can be adjusted:

```bash
agent-index search "playback resolver status" --hybrid --lexical-weight 0.65 --semantic-weight 0.35
```
