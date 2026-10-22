#!/bin/sh
set -eu

REPO_ARCHIVE_URL="${AGENT_INDEX_ARCHIVE_URL:-https://github.com/ElSeniorMikael/agents-embedding-codebase/archive/refs/heads/main.tar.gz}"
INSTALL_DIR="${AGENT_INDEX_INSTALL_DIR:-.agents/embedding-codebase}"
GLOBAL_BIN_DIR="${AGENT_INDEX_GLOBAL_BIN_DIR:-$HOME/.local/bin}"
INSTALL_GLOBAL="${AGENT_INDEX_INSTALL_GLOBAL:-0}"
WITH_OLLAMA=0
for arg in "$@"; do
  case "$arg" in
    --with-ollama) WITH_OLLAMA=1 ;;
    --help|-h) echo "Usage: install.sh [--with-ollama]"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

ensure_python() {
  if python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    return
  fi
  echo "Python 3.10+ is required. Installing Python (may request administrator permission)..."
  case "$(uname -s)" in
    Darwin)
      python_pkg=$(mktemp -d)
      trap 'rm -rf "$python_pkg"' EXIT
      curl -fsSL https://www.python.org/ftp/python/3.14.7/python-3.14.7-macos11.pkg -o "$python_pkg/python.pkg"
      sudo /usr/sbin/installer -pkg "$python_pkg/python.pkg" -target /
      PATH="/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/local/bin:$PATH"
      export PATH
      rm -rf "$python_pkg"
      trap - EXIT
      ;;
    Linux)
      if [ "$(id -u)" = 0 ]; then elevate=""; else elevate="sudo"; fi
      if command -v apt-get >/dev/null 2>&1; then
        $elevate apt-get update
        $elevate apt-get install -y python3
      elif command -v dnf >/dev/null 2>&1; then
        $elevate dnf install -y python3
      elif command -v apk >/dev/null 2>&1; then
        $elevate apk add python3
      else
        echo "No supported package manager found. Install Python 3.10+ and rerun." >&2
        exit 1
      fi
      ;;
    *) echo "Automatic Python installation is unsupported on this OS. Install Python 3.10+ and rerun." >&2; exit 1 ;;
  esac
  if ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    echo "Python installation did not provide Python 3.10+. Check PATH or upgrade Python and rerun." >&2
    exit 1
  fi
}

find_source_dir() {
  script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || true)
  if [ -n "$script_dir" ] && [ -f "$script_dir/project_index.py" ] && [ -d "$script_dir/src" ] && [ -d "$script_dir/bin" ]; then
    printf '%s\n' "$script_dir"
    return 0
  fi
  if [ -f "project_index.py" ] && [ -d "src" ] && [ -d "bin" ]; then
    pwd
    return 0
  fi
  return 1
}

download_source_dir() {
  tmp_dir=$(mktemp -d)
  archive="$tmp_dir/source.tar.gz"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO_ARCHIVE_URL" -o "$archive"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$archive" "$REPO_ARCHIVE_URL"
  else
    echo "agent-index installer: curl or wget is required when installing from a pipe." >&2
    exit 1
  fi
  tar -xzf "$archive" -C "$tmp_dir"
  find "$tmp_dir" -mindepth 1 -maxdepth 1 -type d | head -n 1
}

copy_runtime_files() {
  source_dir="$1"
  destination="$2"
  mkdir -p "$destination"
  mkdir -p "$destination/bin"
  cp "$source_dir/project_index.py" "$destination/project_index.py"
  cp "$source_dir/README.md" "$destination/README.md"
  cp "$source_dir/bin/agent-index" "$destination/bin/agent-index"
  cp "$source_dir/bin/agent-index.cmd" "$destination/bin/agent-index.cmd"
  chmod +x "$destination/bin/agent-index"

  if [ -d "$destination/src" ]; then
    find "$destination/src" -type f -delete
  fi
  mkdir -p "$destination/src"
  find "$source_dir/src" -type f -name '*.py' -exec cp {} "$destination/src/" \;
}

tmp_source=""
ensure_python
if source_dir=$(find_source_dir); then
  :
else
  tmp_source=$(download_source_dir)
  source_dir="$tmp_source"
fi

copy_runtime_files "$source_dir" "$INSTALL_DIR"

if [ "$INSTALL_GLOBAL" = "1" ]; then
  mkdir -p "$GLOBAL_BIN_DIR"
  cp "$INSTALL_DIR/bin/agent-index" "$GLOBAL_BIN_DIR/agent-index"
  chmod +x "$GLOBAL_BIN_DIR/agent-index"
  echo "Installed global dispatcher: $GLOBAL_BIN_DIR/agent-index"
fi

echo "Installed agent-index runtime to: $INSTALL_DIR"
echo "Runtime files: project_index.py, src/, bin/agent-index, README.md"
echo "Run: $INSTALL_DIR/bin/agent-index update"

if [ "$WITH_OLLAMA" = "1" ]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Installing Ollama using its official installer (may request administrator permission)..."
    ollama_installer=$(mktemp)
    trap 'rm -f "$ollama_installer"' EXIT
    if command -v curl >/dev/null 2>&1; then
      curl -fsSL https://ollama.com/install.sh -o "$ollama_installer"
    else
      wget -qO "$ollama_installer" https://ollama.com/install.sh
    fi
    sh "$ollama_installer"
    PATH="/usr/local/bin:$PATH"
    export PATH
  fi
  (cd "$INSTALL_DIR" && python3 -m src.setup_ollama)
fi
