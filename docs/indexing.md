# Indexing

The tool indexes:

- Text/code files under the project root
- Python classes/functions via `ast`
- TypeScript and JavaScript exports, classes, interfaces, type aliases, route paths, and constants via regex
- Markdown headings
- CSS selectors
- SQL tables and indexes
- Local lexical vectors for dependency-free search
- Optional semantic embeddings for meaning-based search
- Python and TypeScript chunks shaped around top-level code symbols, with fixed-line chunking as the fallback

The default excludes skip `node_modules`, virtualenvs, git data, build outputs, dist outputs, caches, binaries, TypeScript build metadata, declaration output, and files larger than 512 KiB.

Add `index.config.json` inside the installed agent folder if you want more project-specific excludes. If installed as `.agents`, use `.agents/index.config.json`:

```json
{
  "exclude": [
    "some/generated/folder/**",
    "large-file.json"
  ]
}
```
