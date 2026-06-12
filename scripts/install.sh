#!/usr/bin/env bash
# Kamil AI Gamer — one-line terminal installer (macOS / Linux).
#
#   curl -LsSf https://raw.githubusercontent.com/k58804494-pixel/ai-roblex-ai/main/scripts/install.sh | bash
#
# Env overrides:
#   KAMIL_REF=main            git ref to install (branch/tag/sha)
#   KAMIL_EXTRAS=all          pip extras (all | vision | control | llm | config | detect)
#   PYTHON=python3            python interpreter to use
set -euo pipefail

REPO="${KAMIL_REPO:-https://github.com/k58804494-pixel/ai-roblex-ai}"
REF="${KAMIL_REF:-main}"
EXTRAS="${KAMIL_EXTRAS:-all}"
SPEC="kamil-ai-gamer[${EXTRAS}] @ git+${REPO}@${REF}"

say() { printf '\033[1;36m[kamil]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[kamil]\033[0m %s\n' "$*" >&2; }

# --- pick a python -----------------------------------------------------------
PYTHON="${PYTHON:-}"
if [ -z "${PYTHON}" ]; then
  for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PYTHON="$c"; break; fi
  done
fi
if [ -z "${PYTHON}" ]; then
  err "Python 3.10+ not found. Install Python first: https://www.python.org/downloads/"
  exit 1
fi
say "Using $(${PYTHON} --version 2>&1)"

# --- optional OCR binary -----------------------------------------------------
if ! command -v tesseract >/dev/null 2>&1; then
  say "Tesseract not found (optional, for OCR fallback)."
  say "  Ubuntu/Debian: sudo apt-get install -y tesseract-ocr"
  say "  macOS:         brew install tesseract"
fi

# --- install -----------------------------------------------------------------
if command -v pipx >/dev/null 2>&1; then
  say "Installing with pipx (isolated)…"
  pipx install --force "${SPEC}"
else
  VENV="${KAMIL_HOME:-$HOME/.kamil-ai-gamer}/venv"
  say "pipx not found — installing into a managed venv at ${VENV}"
  "${PYTHON}" -m venv "${VENV}"
  "${VENV}/bin/pip" install --upgrade pip >/dev/null
  "${VENV}/bin/pip" install "${SPEC}"
  BIN="${HOME}/.local/bin"
  mkdir -p "${BIN}"
  ln -sf "${VENV}/bin/kamil-gamer" "${BIN}/kamil-gamer"
  say "Linked 'kamil-gamer' into ${BIN}"
  case ":${PATH}:" in
    *":${BIN}:"*) : ;;
    *) say "Add ${BIN} to your PATH:  export PATH=\"${BIN}:\$PATH\"" ;;
  esac
fi

say "Installed! Try a safe headless run:"
say "  kamil-gamer --game roblox --cycles 3"
say "No API key needed — for local AI vision/chat install Ollama (https://ollama.com):"
say "  ollama pull llava && ollama pull llama3.2"
