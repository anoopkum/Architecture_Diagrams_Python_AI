#!/usr/bin/env bash
set -euo pipefail

# Run script to setup env, install deps, generate diagrams and convert to drawio
# Usage: ./run.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

echo "Root: $ROOT_DIR"

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv..."
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Installing/Upgrading packaging tools..."
python -m pip install --upgrade pip setuptools wheel

echo "Installing requirements..."
python -m pip install -r "$ROOT_DIR/requirements.txt"

# Ensure graphviz headers are visible (Apple Silicon default)
export CPPFLAGS="-I/opt/homebrew/include"
export LDFLAGS="-L/opt/homebrew/lib"
export PKG_CONFIG_PATH="$(brew --prefix graphviz 2>/dev/null || echo /opt/homebrew/opt/graphviz)/lib/pkgconfig:/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"

echo "Generating diagrams..."
python "$ROOT_DIR/instructions_architecture.py"

DOT_FILE="$ROOT_DIR/diagrams/instructions_architecture.dot"
DRAWIO_FILE="$ROOT_DIR/diagrams/instructions_architecture.drawio"

if command -v graphviz2drawio >/dev/null 2>&1; then
  echo "Converting DOT -> DRAWIO"
  graphviz2drawio "$DOT_FILE" -o "$DRAWIO_FILE" || echo "graphviz2drawio failed"
else
  echo "graphviz2drawio not found in venv; installing..."
  python -m pip install graphviz2drawio
  if command -v graphviz2drawio >/dev/null 2>&1; then
    graphviz2drawio "$DOT_FILE" -o "$DRAWIO_FILE" || echo "graphviz2drawio failed"
  else
    echo "Could not install graphviz2drawio; skipping drawio conversion"
  fi
fi

echo "Done. Outputs in $ROOT_DIR/diagrams"
