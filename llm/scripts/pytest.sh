#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLM_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$LLM_DIR")"

# Ensure the repository root is on PYTHONPATH so `llm` is importable as a package
export PYTHONPATH="$REPO_ROOT:${PYTHONPATH}"

pytest --import-mode=importlib -n 16 --ignore "$LLM_DIR/SWE-agent"   --ignore "$LLM_DIR/demo" "$@"
