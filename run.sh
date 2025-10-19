#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEFAULT_CONFIG_PATH="$SCRIPT_DIR/analyzer_config.yaml"
DEFAULT_LOG_FILE="$SCRIPT_DIR/run.log"
LOG_FILE_DEFAULT="${LOG_FILE:-$DEFAULT_LOG_FILE}"

CONFIG_PATH=""
LOG_FILE=""

prepare_environment() {
	local config_arg="${1:-$DEFAULT_CONFIG_PATH}"
	local log_arg="${2:-$LOG_FILE_DEFAULT}"

	if ! CONFIG_PATH=$(realpath "$config_arg" 2>/dev/null); then
		echo "无法解析配置文件路径: ${1:-$DEFAULT_CONFIG_PATH}" >&2
		return 1
	fi

	if [ ! -f "$CONFIG_PATH" ]; then
		echo "配置文件不存在: $CONFIG_PATH" >&2
		return 1
	fi

	log_arg="${log_arg/#\~/$HOME}"
	if [[ "$log_arg" = /* ]]; then
		LOG_FILE="$log_arg"
	else
		LOG_FILE="$(pwd)/$log_arg"
	fi

	local log_dir
	log_dir=$(dirname -- "$LOG_FILE")
	if ! mkdir -p "$log_dir"; then
		echo "无法创建日志目录: $log_dir" >&2
		return 1
	fi

	rm -f "$LOG_FILE"
	touch "$LOG_FILE"

	export ANALYZER_CONFIG_PATH="$CONFIG_PATH"
	export LOG_FILE
	return 0
}

main() {
	if [ -z "$CONFIG_PATH" ]; then
		echo "配置路径未设置" >&2
		return 1
	fi

	if [ -z "$LOG_FILE" ]; then
		echo "日志路径未设置" >&2
		return 1
	fi

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

prepare_environment "$@" || exit $?

main 2>&1 | tee -a "$LOG_FILE"
exit "${PIPESTATUS[0]}"