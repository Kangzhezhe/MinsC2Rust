#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_CONFIG_PATH="$SCRIPT_DIR/analyzer_config.yaml"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/run.log}"

rm -f "$LOG_FILE"
touch "$LOG_FILE"

main() {
	local config_arg="${1:-$DEFAULT_CONFIG_PATH}"
	local config_path

	if ! config_path=$(realpath "$config_arg"); then
		echo "无法解析配置文件路径: ${1:-$DEFAULT_CONFIG_PATH}" >&2
		return 1
	fi

	if [ ! -f "$config_path" ]; then
		echo "配置文件不存在: $config_path" >&2
		return 1
	fi

	CONFIG_PATH="$config_path"
	export ANALYZER_CONFIG_PATH="$CONFIG_PATH"

	echo "日志输出将保存到: $LOG_FILE"
	echo "使用配置文件: $CONFIG_PATH"

	local rust_output_dir
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
		echo "删除已有输出目录: $rust_output_dir"
		rm -r "$rust_output_dir"
	fi

	(
		cd analyzer
		echo "运行 analyzer/test.sh"
		./test.sh
	)

	python analyzer/build_rust_skeleton.py
	python element_translation.py
	python fill_unimplemented.py
}

main "$@" 2>&1 | tee -a "$LOG_FILE"
exit "${PIPESTATUS[0]}"