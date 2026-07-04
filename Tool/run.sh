#!/bin/bash

set -euo pipefail

DEFAULT_CONFIG_PATH="../configs/config.ini"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)

if [[ -z "${PYTHON_BIN:-}" ]]; then
    if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
        PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
    else
        PYTHON_BIN=$(command -v python3)
    fi
fi

show_usage() {
    cat <<'EOF'
Usage:
  ./run.sh [config_path] [--skip-failed-functions] [--with-non-function-preprocess] [--only-non-function-preprocess]

Options:
  --skip-failed-functions, --skip-failed
      Skip functions already listed in all_error_funcs_content.json
      (forces Params.skip_failed_functions=1 for this run only).
  --with-non-function-preprocess, --with-preprocess
      Run non-function ownership preprocess after makejson.py and before main.py.
  --only-non-function-preprocess, --only-preprocess
      Run makejson.py and then only non-function ownership preprocess; skip main.py.
  -h, --help
      Show this help.
EOF
}

CONFIG_PATH=""
SKIP_FAILED_FUNCTIONS=0
RUN_NON_FUNCTION_PREPROCESS=0
ONLY_NON_FUNCTION_PREPROCESS=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-failed-functions|--skip-failed)
            SKIP_FAILED_FUNCTIONS=1
            shift
            ;;
        --with-non-function-preprocess|--with-preprocess)
            RUN_NON_FUNCTION_PREPROCESS=1
            shift
            ;;
        --only-non-function-preprocess|--only-preprocess)
            RUN_NON_FUNCTION_PREPROCESS=1
            ONLY_NON_FUNCTION_PREPROCESS=1
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [[ -z "$CONFIG_PATH" ]]; then
                CONFIG_PATH="$1"
                shift
            else
                echo "Unexpected argument: $1" >&2
                show_usage >&2
                exit 1
            fi
            ;;
    esac
done

if [[ -z "$CONFIG_PATH" ]]; then
    CONFIG_PATH=$DEFAULT_CONFIG_PATH
    echo "No config path provided. Using default: $CONFIG_PATH"
fi

CONFIG_PATH=$(realpath "$CONFIG_PATH")
cd "$SCRIPT_DIR"

# For iterative convergence runs, keep checkpoints by default.
# Set CLEAN_OUTPUT_ON_START=1 to force a clean slate.
if [[ "${CLEAN_OUTPUT_ON_START:-0}" == "1" && "$CONFIG_PATH" == *"config_c_algorithm"* ]]; then
    CLEAN_ROOT="$REPO_ROOT/Output/c_algorithm"
    if [[ -d "$CLEAN_ROOT" && "$CLEAN_ROOT" == *"/Output/c_algorithm" ]]; then
        echo "[run.sh] Cleaning previous output: $CLEAN_ROOT"
        rm -rf "$CLEAN_ROOT"
    fi
fi

cd "$SCRIPT_DIR/Tool_py"
echo "[run.sh] Python: $PYTHON_BIN" >&2

TMP_CONFIG_PATH=""
cleanup_tmp_config() {
    if [[ -n "$TMP_CONFIG_PATH" && -f "$TMP_CONFIG_PATH" ]]; then
        rm -f "$TMP_CONFIG_PATH"
    fi
}
trap cleanup_tmp_config EXIT

if [[ "$SKIP_FAILED_FUNCTIONS" == "1" ]]; then
    TMP_CONFIG_PATH=$(mktemp)
    "$PYTHON_BIN" - "$CONFIG_PATH" "$TMP_CONFIG_PATH" <<'PY'
import sys
from parse_config import read_config

source_config_path = sys.argv[1]
tmp_config_path = sys.argv[2]
cfg = read_config(source_config_path)

if cfg.has_section("Config"):
    cfg.remove_section("Config")
if not cfg.has_section("Params"):
    cfg.add_section("Params")
cfg.set("Params", "skip_failed_functions", "1")

with open(tmp_config_path, "w", encoding="utf-8") as f:
    cfg.write(f)
PY
    CONFIG_PATH="$TMP_CONFIG_PATH"
    echo "[run.sh] Enabled skip_failed_functions=1 for this run"
fi

RUN_LOG_PATH=$("$PYTHON_BIN" - "$CONFIG_PATH" <<'PY'
import os
import sys
from parse_config import read_config

config_path = sys.argv[1]
cfg = read_config(config_path)

output_dir = cfg.get("Paths", "output_dir", fallback="").strip()
if not output_dir:
    print("")
    sys.exit(0)

print(os.path.join(os.path.abspath(output_dir), "run.log"))
PY
)

if [[ -n "$RUN_LOG_PATH" ]]; then
    mkdir -p "$(dirname "$RUN_LOG_PATH")"
    # Match behavior of: bash ./run.sh ... > run.log
    # - stdout goes to log file
    # - stderr (e.g. progress bars) stays in terminal
    exec 1>>"$RUN_LOG_PATH"
    echo "[run.sh] Run log: $RUN_LOG_PATH" >&2
fi

"$PYTHON_BIN" ./makejson.py "$CONFIG_PATH"

if [[ "$RUN_NON_FUNCTION_PREPROCESS" == "1" ]]; then
    echo "[run.sh] Running non-function ownership preprocess..."
    "$PYTHON_BIN" ./preprocess_non_function_ownership.py "$CONFIG_PATH"
fi

if [[ "$ONLY_NON_FUNCTION_PREPROCESS" == "1" ]]; then
    echo "[run.sh] Preprocess finished. Skipping main.py (--only-non-function-preprocess)."
    exit 0
fi

"$PYTHON_BIN" ./src/main.py "$CONFIG_PATH"
