#!/bin/sh
set -eu

REPO_ARCHIVE_URL="${AGENT_INDEX_ARCHIVE_URL:-https://github.com/ElSeniorMikael/agents-embedding-codebase/archive/refs/heads/main.tar.gz}"
INSTALL_DIR="${AGENT_INDEX_INSTALL_DIR:-.agents}"
GLOBAL_BIN_DIR="${AGENT_INDEX_GLOBAL_BIN_DIR:-$HOME/.local/bin}"
INSTALL_GLOBAL="${AGENT_INDEX_INSTALL_GLOBAL:-0}"

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
  chmod +x "$destination/bin/agent-index"

  if [ -d "$destination/src" ]; then
    find "$destination/src" -type f -delete
  fi
  mkdir -p "$destination/src"
  find "$source_dir/src" -type f -name '*.py' -exec cp {} "$destination/src/" \;
}

tmp_source=""
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
