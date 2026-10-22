# Agent Project Index

Local vector/text indexing for AI agents. Copy this folder into any project so agents can search the codebase without rereading the whole tree every time.

## Install / Setup

Python 3.10 or newer is required. Indexing and lexical search need no extra Python packages or embedding service.

For semantic or hybrid search, choose **Ollama with `nomic-embed-text`** (the default) or **OpenAI with `OPENAI_API_KEY`**. Both installers check for Python 3.10+ before copying runtime files and install it when missing or too old. By default, the installer does not install Ollama or its embedding model; opt in with `--with-ollama` on macOS/Linux or `-WithOllama` on Windows.

### macOS

Run these commands in Terminal from your project root. A compatible `python3` is reused. Otherwise the installer downloads the official Python 3.14.7 macOS package and installs it with `sudo`; enter your administrator password when prompted.

#### Install

Install the runtime into `.agents/embedding-codebase/`:

```bash
cd /path/to/your-project
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | sh
```

Build the index and try lexical search immediately:

```bash
python3 .agents/embedding-codebase/project_index.py update
python3 .agents/embedding-codebase/project_index.py search "task topic"
```

To install or update the optional global `agent-index` dispatcher:

```bash
mkdir -p "$HOME/.local/bin"
cp .agents/embedding-codebase/bin/agent-index "$HOME/.local/bin/agent-index"
chmod +x "$HOME/.local/bin/agent-index"
export PATH="$HOME/.local/bin:$PATH"
```

Add the `export PATH` line to your shell profile (for example, `~/.zshrc`) to keep it available in new terminals. Then run `agent-index update` or `agent-index search "task topic"` from anywhere inside the project. Repeat the copy command after upgrading an older dispatcher so it recognizes the nested installation.

You can also install the runtime and global dispatcher together:

```bash
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | AGENT_INDEX_INSTALL_GLOBAL=1 sh
```

#### Enable semantic search

To install Ollama if missing and download the default embedding model in one step:

```bash
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | sh -s -- --with-ollama
```

From a local checkout, use `./install.sh --with-ollama`. The flag reuses an existing `ollama` command; otherwise it runs [Ollama's official installer](https://ollama.com/download), which may request administrator permission. It downloads `nomic-embed-text`, an embedding model, and may take time and disk space. A server already running is left running; a temporary server started for the model download is stopped afterward. Run `embed` separately to build project embeddings.

If you prefer manual setup, install Ollama separately, then pull the model. The following commands also work after automatic setup (the pull reuses an up-to-date model):

```bash
ollama pull nomic-embed-text
python3 .agents/embedding-codebase/project_index.py embed
python3 .agents/embedding-codebase/project_index.py search "task topic" --hybrid
```

Alternatively, use OpenAI embeddings:

```bash
export OPENAI_API_KEY="your-api-key"
python3 .agents/embedding-codebase/project_index.py embed --provider openai
python3 .agents/embedding-codebase/project_index.py search "task topic" --hybrid
```

### Windows

Use the native PowerShell installer (PowerShell 5.1 or newer). The installer checks `python` and `py -3` for Python 3.10+. If neither is suitable, it downloads the official Python 3.14.7 installer for your architecture and installs it for your user, adding it to PATH. Git and a Unix shell are not required.

#### Install with PowerShell

From your project root, download the installer and run it:

```powershell
Set-Location C:\path\to\your-project
$installer = Join-Path $env:TEMP "agent-index-install.ps1"
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.ps1" -OutFile $installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
Remove-Item -LiteralPath $installer
```

After ensuring Python is available, this copies the runtime into `.agents/embedding-codebase/`. The execution-policy option applies to this PowerShell process, without changing your saved policy.

Use the local launcher to build and search the index:

```powershell
& .\.agents\embedding-codebase\bin\agent-index.cmd update
& .\.agents\embedding-codebase\bin\agent-index.cmd search "task topic"
```

The launcher detects `python` or `py -3`, requires Python 3.10+, and preserves the command's exit code. It can also be called from Command Prompt.

For an optional global command, add `-InstallGlobal` to the installer invocation above. It copies the launcher and dispatcher to `%LOCALAPPDATA%\agent-index\bin`. Add that folder to your user PATH through Windows environment settings and open a new terminal. Then `agent-index update` and `agent-index search "task topic"` work from any project subdirectory.

Installer options: `-InstallDir` selects another runtime folder; `-GlobalBinDir` selects the global command folder. The `AGENT_INDEX_INSTALL_DIR`, `AGENT_INDEX_INSTALL_GLOBAL=1`, and `AGENT_INDEX_GLOBAL_BIN_DIR` environment variables are also supported. Re-running the installer updates runtime files while preserving the index cache and `index.config.json`.

Open a new terminal after automatic Python installation to pick up its PATH changes. The installer itself uses the newly installed Python immediately.

Native Windows execution is covered by the Windows CI job; it cannot be validated on macOS alone.

#### Enable semantic search

To install Ollama if missing and download `nomic-embed-text`, add `-WithOllama` to the PowerShell installer invocation **before** removing the downloaded script:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer -WithOllama
```

You can combine this with `-InstallGlobal`. From a local checkout, use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -WithOllama`. The flag uses Ollama's official Windows installer if needed, reuses an existing installation, and pulls the embedding model. Complete any installer prompts. The Python prerequisite is handled automatically. Open a new terminal afterward if Ollama was added to your user PATH.

For manual setup, install Ollama for Windows separately. Then pull the model and build the project's embeddings:

```powershell
ollama pull nomic-embed-text
& .\.agents\embedding-codebase\bin\agent-index.cmd embed
& .\.agents\embedding-codebase\bin\agent-index.cmd search "task topic" --hybrid
```

Alternatively, use OpenAI embeddings:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
& .\.agents\embedding-codebase\bin\agent-index.cmd embed --provider openai
& .\.agents\embedding-codebase\bin\agent-index.cmd search "task topic" --hybrid
```

If you use WSL instead, run the shell commands from the macOS section inside WSL, with your chosen embedding backend available there. On Linux/WSL, missing or outdated Python triggers installation through `apt-get`, `dnf`, or `apk`, with `sudo` when needed. Older distributions whose packages still provide Python below 3.10 must be upgraded or configured with a newer Python before rerunning. WSL setup has not yet been validated.

### Installation layout and configuration

The default layout indexes the project containing `.agents` and keeps runtime files and generated caches together:

```text
your-project/
  .agents/
    embedding-codebase/
      project_index.py
      bin/
        agent-index
        agent-index.cmd      # Windows launcher
      README.md
      src/
      index/                 # generated on first use
```

Add `.agents/embedding-codebase/index/` to your project's `.gitignore`. Add `.agents/embedding-codebase/index.config.json` for project-specific file exclusions.

For a different installation folder, set `AGENT_INDEX_INSTALL_DIR` when running the shell installer:

```bash
curl -fsSL https://raw.githubusercontent.com/ElSeniorMikael/agents-embedding-codebase/main/install.sh | AGENT_INDEX_INSTALL_DIR=.codex sh
```

Existing direct installations in `.agents`, `.codex`, `.cursor-agent`, or `.agent-index` still work and index their parent directory. A runtime directly inside `.agents/` indexes the project containing `.agents`. For other layouts, set `AGENT_INDEX_ROOT` to override the default parent directory. If using the global dispatcher with a custom path, set `AGENT_INDEX_DIR_NAMES` to that project-relative path. Separate multiple paths with `:` on macOS/Linux or `;` on Windows.

## Agent startup rule

Add the following rule to your project's `AGENTS.md` or your agent's equivalent project rules file so the index stays current across tasks and chats:

```text
At the start of every new task or chat, run `agent-index update` from inside
the project before searching the index or scoping implementation work.
Use the refreshed index to find relevant files, then read those files before editing.
If semantic or hybrid search reports missing or stale embeddings, run
`agent-index embed` with the configured provider before retrying the search.
```

If you did not install the global dispatcher, replace `agent-index` in the rule with `python3 .agents/embedding-codebase/project_index.py` on macOS or `& .\.agents\embedding-codebase\bin\agent-index.cmd` in Windows PowerShell, and run it from the project root.

`agent-index update` is incremental, so unchanged files do not need to be rechunked. See [Agent Workflow](docs/agent-workflow.md) for search guidance.

## Tests

GitHub Actions runs the test suite on Ubuntu and Windows with Python 3.10 and 3.12 for pushes and pull requests. You can also run the **Tests** workflow manually from the repository's Actions tab.

Windows integration tests exercise PowerShell installation from a checkout and a downloaded ZIP, local and global `.cmd` launchers, paths with spaces, search from project subdirectories, cache/configuration preservation on reinstall, and error exit codes. Downloads use a local test server containing the current checkout. CI does not install Ollama or download the real embedding model; model setup behavior is covered with mocked tests.

Run the suite locally with `python -m unittest discover -s tests -v` (use `python3` on macOS). Native Windows installer tests are skipped on other operating systems.

## References

- [Commands](docs/commands.md)
- [Agent Workflow](docs/agent-workflow.md)
- [Search Modes](docs/search-modes.md)
- [Semantic Embeddings](docs/semantic-embeddings.md)
- [Indexing](docs/indexing.md)
- [Troubleshooting](docs/troubleshooting.md)
