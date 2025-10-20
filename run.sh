#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
RUN_ID=$(date +"%Y%m%d-%H%M%S")-$$
DEFAULT_CONFIG_PATH="$SCRIPT_DIR/analyzer_config.yaml"
DEFAULT_LOG_DIR="$SCRIPT_DIR/logs"
DEFAULT_LOG_FILE="$DEFAULT_LOG_DIR/run-$RUN_ID.log"
LOG_FILE_DEFAULT="${LOG_FILE:-$DEFAULT_LOG_FILE}"

CONFIG_PATH=""
LOG_FILE=""
FILL_ONLY=0

usage() {
	cat <<'EOF'
用法: run.sh [配置文件路径] [日志文件路径] [--fill-only]

参数:
  配置文件路径   可选，默认使用脚本同目录下的 analyzer_config.yaml
  日志文件路径   可选，默认写入 logs/run-<时间>-<pid>.log

选项:
  --fill-only    仅运行 python fill_unimplemented.py，跳过 analyzer/test 与前置构建
  -h, --help     显示本帮助并退出
EOF
}

POSITIONAL_ARGS=()
for arg in "$@"; do
	case "$arg" in
		--fill-only)
			FILL_ONLY=1
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			POSITIONAL_ARGS+=("$arg")
			;;
	esac
done
set -- "${POSITIONAL_ARGS[@]}"

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

	: > "$LOG_FILE"

	export ANALYZER_CONFIG_PATH="$CONFIG_PATH"
	export LOG_FILE
	return 0
}

start_logging() {
	if command -v stdbuf >/dev/null 2>&1; then
		exec > >(stdbuf -oL -eL tee -a "$LOG_FILE") 2>&1
	else
		exec > >(tee -a "$LOG_FILE") 2>&1
	fi
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

	if [ "$FILL_ONLY" -eq 0 ]; then
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
	else
		echo "启用 --fill-only，跳过 analyzer/test.sh 与前置构建。"
	fi
	python fill_unimplemented.py
}

prepare_environment "$@" || exit $?
start_logging

main
exit $?