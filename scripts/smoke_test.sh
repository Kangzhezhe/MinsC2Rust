#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"
.venv/bin/python Tool/Tool_py/smoke_runner.py run-arraylist-reference-smoke \
  --tool-py-root Tool/Tool_py \
  --base-config configs/config.ini \
  --derived-config /tmp/tool_py_arraylist_real_smoke_reference_aligned.ini \
  --output-root "${ROOT_DIR}/Output/arraylist_smoke_current" \
  --reference-output "${ROOT_DIR}/Output/arraylist/Output" \
  --clean-output
