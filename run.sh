set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_CONFIG_PATH="$SCRIPT_DIR/analyzer_config.yaml"

CONFIG_PATH="${1:-$DEFAULT_CONFIG_PATH}"

if ! CONFIG_PATH=$(realpath "$CONFIG_PATH"); then
	echo "无法解析配置文件路径: ${1:-$DEFAULT_CONFIG_PATH}" >&2
	exit 1
fi

if [ ! -f "$CONFIG_PATH" ]; then
	echo "配置文件不存在: $CONFIG_PATH" >&2
	exit 1
fi

export ANALYZER_CONFIG_PATH="$CONFIG_PATH"

rust_output_dir=$(python - <<'PYTHON'
import sys
from analyzer.config import load_rust_output_dir

try:
	path = load_rust_output_dir()
except Exception as exc:
	print(f"读取 rust_output 失败: {exc}", file=sys.stderr)
	sys.exit(1)

if path is None:
	print("配置文件未设置 rust_output", file=sys.stderr)
	sys.exit(1)

print(path.as_posix())
PYTHON
)

if [ -d "$rust_output_dir" ]; then
	rm -r "$rust_output_dir"
fi
cd analyzer && ./test.sh
cd ..
python analyzer/build_rust_skeleton.py
python element_translation.py
python fill_unimplemented.py