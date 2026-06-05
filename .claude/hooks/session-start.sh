#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code on the web sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install dependencies based on what's present in the repo
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if [ -f "$REPO/package.json" ]; then
  echo "Installing Node.js dependencies..."
  cd "$REPO" && npm install
elif [ -f "$REPO/requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r "$REPO/requirements.txt" --quiet
elif [ -f "$REPO/pyproject.toml" ]; then
  echo "Installing Python dependencies (pyproject.toml)..."
  pip install -e "$REPO" --quiet
elif [ -f "$REPO/Cargo.toml" ]; then
  echo "Fetching Rust dependencies..."
  cd "$REPO" && cargo fetch
elif [ -f "$REPO/go.mod" ]; then
  echo "Downloading Go dependencies..."
  cd "$REPO" && go mod download
else
  echo "No dependency manifest found — skipping dependency install."
fi

echo "Session start hook complete."
