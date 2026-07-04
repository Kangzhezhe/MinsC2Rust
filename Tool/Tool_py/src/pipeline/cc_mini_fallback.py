"""CC-MINI fallback and SWE-style repair support.

This is a core capability, not optional glue. The main pipeline calls into this
module when ordinary LLM repair cannot make progress or when runtime test
feedback needs a sandboxed Cargo project plus command/debug tooling.
"""

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from utils import (
    dedupe_non_function_content,
    is_rust_snippet_brace_balanced,
    normalize_rust_module_name,
    split_rust_code_structural,
)
from pipeline.stats import (
    increment_roundtrip_verify_failure_count,
    increment_roundtrip_verify_success_count,
    record_ast_split_result,
)


class CcMiniFallbackCoordinator:
    """CC-MINI assisted repair behavior used by `TranslationPipeline`."""

    @staticmethod
    def _collapse_whitespace(text: str) -> str:
        """Normalize command text before comparing acceptance commands."""
        return " ".join(str(text or "").split())

    @staticmethod
    def _extract_rust_function_name_from_code(code: str) -> str:
        text = (code or "").strip()
        if not text:
            return ""
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue
            match = re.search(r"\bfn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", stripped)
            return match.group(1) if match else ""
        return ""

    def _ensure_swe_runtime_debug_tool(self, agent) -> None:
        """Expose the Rust debug helper to the active CC-MINI agent session."""
        if agent is None:
            return

        toolset = getattr(agent, "toolset", None)
        if toolset is not None and hasattr(toolset, "debug_script_dependency_overrides"):
            toolset.debug_script_dependency_overrides.clear()
            toolset.debug_script_dependency_overrides.update(self.project_dependency_overrides)

        tools_map = getattr(agent, "tools", {}) or {}
        if "run_rust_debug_script" in tools_map:
            return
        debug_tool = getattr(toolset, "run_rust_debug_script", None)
        if debug_tool is None:
            return
        existing_tools = list(tools_map.values())
        existing_names = {getattr(t, "__name__", "") for t in existing_tools}
        if "run_rust_debug_script" not in existing_names:
            existing_tools.append(debug_tool)
        try:
            agent.register_tools(existing_tools)
            self.logger.info("[CC-MINI-TOOL-ENABLE] runtime debug tool enabled for current CC-MINI session")
        except Exception as exc:
            self.logger.info(f"[CC-MINI-TOOL-ENABLE-FAIL] runtime debug tool err={exc}")

    def _verify_runtime_roundtrip_archive(
        self,
        *,
        archive: Dict[str, Dict[str, str]],
        export_sources: List[str],
        test_sources: List[str],
        crate_name: str,
        label: str,
    ) -> Tuple[bool, str]:
        base_tmp_dir = os.path.abspath(getattr(self.verifier, "base_tmp_dir", tempfile.gettempdir()))
        os.makedirs(base_tmp_dir, exist_ok=True)
        timeout = int(getattr(self, "test_runtime_check_timeout_seconds", 120) or 120)

        with tempfile.TemporaryDirectory(
            prefix=f"roundtrip_runtime_{normalize_rust_module_name(label)}_",
            dir=base_tmp_dir,
        ) as roundtrip_root:
            ok, msg = self.export_archive_to_project(
                archive=archive,
                include_files=export_sources,
                output_project_path=roundtrip_root,
                crate_name=crate_name,
            )
            if not ok:
                increment_roundtrip_verify_failure_count()
                return False, f"round-trip cargo test export src failed: {msg}"

            test_ok, test_msg = self.export_archive_tests_to_project(
                archive=archive,
                include_test_files=test_sources,
                output_project_path=roundtrip_root,
                crate_name=crate_name,
            )
            if not test_ok:
                increment_roundtrip_verify_failure_count()
                return False, f"round-trip cargo test export tests failed: {test_msg}"

            try:
                env = os.environ.copy()
                shared_target_dir = os.path.join(base_tmp_dir, "cargo_target_shared")
                os.makedirs(shared_target_dir, exist_ok=True)
                env["CARGO_TARGET_DIR"] = shared_target_dir
                proc = subprocess.run(
                    ["cargo", "test", "--quiet"],
                    cwd=roundtrip_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    timeout=timeout,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                increment_roundtrip_verify_failure_count()
                return False, f"round-trip cargo test timeout after {timeout}s"

            output = "\n".join([(proc.stderr or "").strip(), (proc.stdout or "").strip()]).strip()
            if proc.returncode == 0:
                increment_roundtrip_verify_success_count()
                self.logger.info(f"[ROUNDTRIP-TEST-PASS] {label} cargo test passed")
                return True, "round-trip cargo test passed"

            increment_roundtrip_verify_failure_count()
            return (
                False,
                "round-trip cargo test failed: "
                + self._clip_text(output or f"returncode={proc.returncode}", 1600),
            )

    def _run_test_module_with_optional_swe_repair(
        self,
        *,
        test_source_name: str,
        source_name: str,
        func_name: str,
        include_files: List[str],
        archive: Dict[str, Dict[str, str]],
        source_level: bool = False,
    ) -> Tuple[bool, str, Optional[Dict[str, Dict[str, str]]]]:
        """Run translated Rust tests and optionally let CC-MINI repair failures."""
        if not self.test_runtime_check_enabled:
            return True, "runtime test check disabled", None
        runtime_mode = str(getattr(self, "test_runtime_check_mode", "function") or "function").strip().lower()
        if runtime_mode == "off":
            return True, "runtime test check disabled", None
        if runtime_mode == "source_complete" and not source_level:
            return True, "runtime test check deferred to source completion", None
        if runtime_mode == "function" and source_level:
            return True, "source-level runtime test check disabled in function mode", None
        if not self._is_test_source(source_name):
            return True, "non-test source", None
        if not source_level and not func_name.startswith("test_"):
            return True, "non-test function", None

        project_root = os.path.join(
            os.path.abspath(getattr(self.verifier, "base_tmp_dir", tempfile.gettempdir())),
            "verify_project_runtime",
            normalize_rust_module_name(test_source_name),
            normalize_rust_module_name(source_name),
        )
        os.makedirs(project_root, exist_ok=True)

        # Runtime check now executes full `cargo test`, so sandbox must always contain
        # the full non-test crate surface (all src modules), not only current include scope.
        export_sources = [
            name for name in archive.keys() if not self._is_test_source(name)
        ]
        if not export_sources:
            return False, "runtime test check skipped: no exportable src modules", None

        crate_name = "verify_project"
        ok, msg = self.export_archive_to_project(
            archive=archive,
            include_files=export_sources,
            output_project_path=project_root,
            crate_name=crate_name,
        )
        if not ok:
            return False, f"runtime test check export src failed: {msg}", None

        all_test_sources = [name for name in archive.keys() if self._is_test_source(name)]
        if source_name not in all_test_sources:
            all_test_sources.append(source_name)

        test_ok, test_msg = self.export_archive_tests_to_project(
            archive=archive,
            include_test_files=all_test_sources,
            output_project_path=project_root,
            crate_name=crate_name,
        )
        if not test_ok:
            return False, f"runtime test check export tests failed: {test_msg}", None

        tests_dir = os.path.join(project_root, "tests")
        module_name = normalize_rust_module_name(source_name)
        test_file = os.path.join(tests_dir, f"{module_name}.rs")
        if not os.path.isdir(tests_dir) or not os.path.isfile(test_file):
            return False, "runtime test check missing verify_project/tests module file", None

        test_cmd = ["cargo", "test", "--quiet"]

        def run_direct_test() -> Tuple[bool, str]:
            try:
                env = os.environ.copy()
                shared_target_dir = os.path.join(
                    os.path.abspath(getattr(self.verifier, "base_tmp_dir", tempfile.gettempdir())),
                    "cargo_target_shared",
                )
                os.makedirs(shared_target_dir, exist_ok=True)
                env["CARGO_TARGET_DIR"] = shared_target_dir

                proc = subprocess.run(
                    test_cmd,
                    cwd=project_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    timeout=self.test_runtime_check_timeout_seconds,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                return False, f"cargo test timeout after {self.test_runtime_check_timeout_seconds}s"
            output = "\n".join([(proc.stderr or "").strip(), (proc.stdout or "").strip()]).strip()
            if proc.returncode == 0:
                return True, "cargo test passed"
            return False, self._clip_text(output or f"cargo test failed returncode={proc.returncode}", 1600)

        passed, detail = run_direct_test()
        if passed:
            return True, detail, None

        if not self.enable_cc_mini_agent_fallback:
            return False, "runtime cargo test failed (no CC-MINI fallback): " + detail, None

        swe_summary = ""
        for attempt in range(1, self.test_runtime_swe_max_attempts + 1):
            agent = self._get_cc_mini_agent_instance(project_root)
            if agent is None:
                return False, "runtime cargo test failed and CC-MINI Agent unavailable: " + detail, None
            self._ensure_swe_runtime_debug_tool(agent)

            scope_label = "测试源" if source_level else "测试模块"
            task = "".join(
                [
                    f"当前{scope_label} `{source_name}` 的测试运行失败。请修复工程并确保命令通过。\n",
                    f"测试用例本身的逻辑也可能有问题，允许在有充分理由时修改测试。\n"
                    f"由于代码是从C翻译过来的，如果代码本身在内存上不是Rust风格，允许重构为Rust安全惯用风格\n"
                    f"注意：不要更改函数名或删除已有的函数，但是可以按需添加函数\n",
                    "必须执行并通过：cargo test --quiet\n",
                    "你可以使用工具 `run_rust_debug_script(script_code)` 做行为调试，多设计可复现实验帮助定位错误根因，打印关键中间状态，辅助诊断错误：\n"
                    "- 仅提供脚本正文（不需要 shebang/cargo 头）；工具会自动保存并执行；\n"
                    "- 调试脚本默认优先 `use verify_project::<module>::...` 复用已有模块/类型/函数；\n"
                    "- 若定位困难，可采用半隔离：仅抽取目标函数 + 必需的非函数元素（type/const/static）完整定义到脚本中，其余依赖保持 use 模式；\n"
                    "- 禁止重复定义大量同名 API；如需本地对照实现，请使用 `debug_` 前缀避免同名冲突；\n"
                    "- 符号导入优先参考 tests 文件中的现有 use 语句。\n",
                    "当测试主要约束 C 特有内存模型（如裸指针生命周期、分配器内部计数/limit/allocation_limit 细节）且与 Rust 安全内存语义冲突时，可在给出明确理由后调整测试：\n"
                    "- 调整原则：保留函数功能/语义一致性断言，仅替换删除实现机制耦合断言（memory-model-specific assertions）；\n"
                ]
            )
            try:
                run_task_result = agent.run_task(
                    task,
                    acceptance_criteria=[
                        "必须执行 `cargo test --quiet` 且返回码为0",
                    ],
                )
                swe_summary = self._summarize_cc_mini_agent_result(run_task_result)
            except Exception as exc:
                detail = f"CC-MINI run_task 异常: {exc}"
                continue

            try:
                rerun = agent.toolset.run_command("cargo test --quiet")
                rc = int((rerun or {}).get("returncode", 1))
                out = self._summarize_tool_output(rerun, max_lines=60)
            except Exception as exc:
                rc = 1
                out = f"复验异常: {exc}"

            if rc == 0:
                self._update_dependency_overrides_from_cargo_toml(
                    os.path.join(project_root, "Cargo.toml"),
                    log_label=f"runtime:{test_source_name}:{func_name}",
                )
                candidate_results = copy.deepcopy(archive)
                for src in export_sources:
                    src_module = normalize_rust_module_name(src)
                    src_path = os.path.join(project_root, "src", f"{src_module}.rs")
                    if not os.path.isfile(src_path):
                        continue
                    try:
                        with open(src_path, "r", encoding="utf-8") as f:
                            text = f.read()
                        rebuilt_bucket, rebuilt_error = self._rebuild_bucket_from_module_text(
                            src,
                            text,
                            previous_bucket=archive.get(src, {}),
                        )
                        if rebuilt_error or not rebuilt_bucket:
                            continue
                        candidate_results[src] = rebuilt_bucket
                    except Exception:
                        continue

                rebuilt_current_test = False
                for test_src in all_test_sources:
                    test_module = normalize_rust_module_name(test_src)
                    test_path = os.path.join(tests_dir, f"{test_module}.rs")
                    if not os.path.isfile(test_path):
                        continue
                    try:
                        with open(test_path, "r", encoding="utf-8") as f:
                            test_text = f.read()
                        test_text = test_text.replace(f"use {crate_name}::", "use crate::")
                        test_text = test_text.replace(f"{crate_name}::", "crate::")
                        rebuilt_test_bucket, rebuilt_test_error = self._rebuild_bucket_from_module_text(
                            test_src,
                            test_text,
                            required_func=(
                                "" if source_level or test_src != source_name else func_name
                            ),
                            previous_bucket=archive.get(test_src, {}),
                        )
                        if rebuilt_test_error or not rebuilt_test_bucket:
                            if test_src == source_name:
                                return (
                                    False,
                                    "runtime cargo test passed but test module回灌失败: "
                                    + (rebuilt_test_error or "empty rebuilt bucket"),
                                    None,
                                )
                            self.logger.info(
                                f"[TEST-REBUILD-SKIP] {test_src} error={rebuilt_test_error or 'empty rebuilt bucket'}"
                            )
                            continue
                        candidate_results[test_src] = rebuilt_test_bucket
                        if test_src == source_name:
                            rebuilt_current_test = True
                    except Exception as exc:
                        if test_src == source_name:
                            return False, f"runtime cargo test passed but读取测试模块失败: {exc}", None
                        self.logger.info(f"[TEST-REBUILD-SKIP] {test_src} error={exc}")

                if not rebuilt_current_test:
                    return False, "runtime cargo test passed but current test module was not rebuilt", None

                roundtrip_ok, roundtrip_detail = self._verify_runtime_roundtrip_archive(
                    archive=candidate_results,
                    export_sources=export_sources,
                    test_sources=all_test_sources,
                    crate_name=crate_name,
                    label=f"{test_source_name}:{func_name}",
                )
                if not roundtrip_ok:
                    self.logger.info(
                        f"[ROUNDTRIP-TEST-FAIL] {test_source_name}:{func_name} detail={roundtrip_detail[:260]}"
                    )
                    return False, roundtrip_detail, None

                return True, "runtime cargo test passed via CC-MINI", candidate_results

            detail = self._clip_text(out, 1600)
            self.logger.info(
                f"[TEST-RUNTIME-CC-MINI-FAIL] {test_source_name}:{func_name} attempt={attempt}/{self.test_runtime_swe_max_attempts} detail={detail[:260]}"
            )

        tail = f"\n[CC-MINI run]\n{swe_summary}" if swe_summary else ""
        return False, "runtime cargo test failed after CC-MINI attempts: " + detail + tail, None

    def _run_source_module_with_optional_swe_repair(
        self,
        *,
        test_source_name: str,
        source_name: str,
        include_files: List[str],
        archive: Dict[str, Dict[str, str]],
    ) -> Tuple[bool, str, Optional[Dict[str, Dict[str, str]]]]:
        return self._run_test_module_with_optional_swe_repair(
            test_source_name=test_source_name,
            source_name=source_name,
            func_name="__source_complete__",
            include_files=include_files,
            archive=archive,
            source_level=True,
        )

    @staticmethod
    def _parse_dependency_overrides_from_cargo_toml(cargo_toml_text: str) -> Dict[str, str]:
        text = str(cargo_toml_text or "")
        if not text.strip():
            return {}

        in_dependencies = False
        overrides: Dict[str, str] = {}
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                in_dependencies = line == "[dependencies]"
                continue
            if not in_dependencies:
                continue
            if "=" not in line:
                continue
            name, value = line.split("=", 1)
            dep_name = name.strip()
            dep_value = value.strip()
            if not dep_name or dep_name == "libc":
                continue
            overrides[dep_name] = dep_value
        return overrides

    def _sync_dependency_overrides_to_verifier(self) -> None:
        if hasattr(self.verifier, "dependency_overrides"):
            self.verifier.dependency_overrides = dict(self.project_dependency_overrides)

    def _update_dependency_overrides_from_cargo_toml(
        self,
        cargo_toml_path: str,
        log_label: str = "",
    ) -> int:
        if not cargo_toml_path or not os.path.isfile(cargo_toml_path):
            return 0
        try:
            with open(cargo_toml_path, "r", encoding="utf-8") as f:
                cargo_text = f.read()
        except Exception:
            return 0

        parsed = self._parse_dependency_overrides_from_cargo_toml(cargo_text)
        if not parsed:
            return 0

        changed = 0
        for name, value in parsed.items():
            prev = self.project_dependency_overrides.get(name)
            if prev == value:
                continue
            self.project_dependency_overrides[name] = value
            changed += 1

        if changed > 0:
            self._sync_dependency_overrides_to_verifier()
            self.logger.info(
                f"[DEPENDENCY-OVERRIDE] {log_label} updated={changed} deps={','.join(sorted(parsed.keys())[:12])}"
            )
        return changed

    @staticmethod
    def _summarize_tool_output(result: Dict[str, Any], max_lines: int = 20) -> str:
        if not isinstance(result, dict):
            return str(result)
        stderr = str(result.get("stderr", "") or "").strip()
        stdout = str(result.get("stdout", "") or "").strip()
        combined = "\n".join([part for part in (stderr, stdout) if part]).strip()
        if not combined:
            return "(empty output)"
        return "\n".join(combined.splitlines()[:max_lines])

    def _summarize_cc_mini_agent_result(self, run_task_result: Any) -> str:
        if not isinstance(run_task_result, dict):
            return self._clip_text(str(run_task_result), 1200)

        lines: List[str] = []
        success = bool(run_task_result.get("success", False))
        iterations = run_task_result.get("iterations", "?")
        error_msg = (run_task_result.get("error", "") or "").strip()
        final_response = (run_task_result.get("final_response", "") or "").strip()
        tool_calls = run_task_result.get("tool_calls") or []

        lines.append(f"success={success} iterations={iterations} tool_calls={len(tool_calls)}")
        if error_msg:
            lines.append(f"error={self._clip_text(error_msg, 300)}")
        if final_response:
            lines.append("final_response=")
            lines.append(self._clip_text(final_response, 700))

        for idx, call in enumerate(tool_calls[-5:], start=max(1, len(tool_calls) - 4)):
            if not isinstance(call, dict):
                lines.append(f"tool#{idx}: {self._clip_text(str(call), 260)}")
                continue
            name = str(call.get("name", "")).strip() or "unknown"
            args = self._clip_text(json.dumps(call.get("args", {}), ensure_ascii=False), 220)
            result_text = self._clip_text(str(call.get("result", "") or ""), 280)
            lines.append(f"tool#{idx} {name} args={args}")
            if result_text:
                lines.append(f"tool#{idx} result={result_text}")

        return "\n".join(lines).strip()

    def _cargo_output_has_error_markers(self, result: Any) -> bool:
        if not isinstance(result, dict):
            return False

        stdout = str(result.get("stdout", "") or "")
        stderr = str(result.get("stderr", "") or "")
        combined = "\n".join(part for part in (stderr, stdout) if part)
        if not combined.strip():
            return False

        patterns = [
            r"(?m)^\s*error\[E\d{4}\]:",
            r"(?m)^\s*error:",
            r"(?m)^\s*\[error\]\s*E?\d{0,4}",
            r"\bcould not compile\b",
        ]
        return any(re.search(pat, combined, flags=re.IGNORECASE) for pat in patterns)

    def _validate_swe_acceptance_command(
        self,
        run_task_result: Any,
        compile_cmd: str,
    ) -> Tuple[bool, str]:
        if not isinstance(run_task_result, dict):
            return False, "CC-MINI run_task 缺少可校验的 tool_calls 记录"

        compile_cmd_norm = self._collapse_whitespace(compile_cmd)
        tool_calls = run_task_result.get("tool_calls") or []
        saw_exact = False
        saw_exact_success = False
        saw_exact_error_output = False
        wrapped_commands: List[str] = []

        for call in tool_calls:
            if not isinstance(call, dict):
                continue
            if str(call.get("name", "")).strip() != "run_command":
                continue

            args = call.get("args", {}) or {}
            command = self._collapse_whitespace(str(args.get("command", "") or ""))
            if not command or not compile_cmd_norm or compile_cmd_norm not in command:
                continue

            result = call.get("result", {}) or {}
            try:
                returncode = int(result.get("returncode", 1))
            except Exception:
                returncode = 1

            if command == compile_cmd_norm:
                saw_exact = True
                if returncode == 0:
                    if self._cargo_output_has_error_markers(result):
                        saw_exact_error_output = True
                    else:
                        saw_exact_success = True
            else:
                wrapped_commands.append(command)

        if saw_exact_success:
            return True, ""
        if saw_exact_error_output:
            return False, (
                f"CC-MINI 执行了 `{compile_cmd}` 且返回码为 0，但输出仍包含编译错误标记"
            )
        if saw_exact:
            return False, f"CC-MINI 执行了 `{compile_cmd}`，但返回码非 0"
        if wrapped_commands:
            return False, (
                "CC-MINI 未直接执行保留原始退出码的验收命令；检测到包装命令: "
                + " | ".join(wrapped_commands[:3])
            )
        return False, f"CC-MINI 未执行要求的原始验收命令 `{compile_cmd}`"

    def _compose_regen_prompt_with_swe_notes(
        self,
        base_prompt: str,
        swe_notes: List[str],
    ) -> str:
        if not swe_notes:
            return base_prompt

        rendered_notes: List[str] = []
        recent_notes = swe_notes[-self.swe_regen_assist_max_notes :]
        for idx, note in enumerate(recent_notes, start=1):
            text = self._clip_text(str(note or "").strip(), self.swe_regen_assist_note_max_chars)
            if not text:
                continue
            rendered_notes.append(f"[CC-MINI失败归因#{idx}]\n{text}")

        if not rendered_notes:
            return base_prompt

        return (
            base_prompt
            + "\n\n"
            + "上轮 gen/regen 后 CC-MINI Agent 单次修复失败归因（用于下一轮避免重复）：\n"
            + "\n\n".join(rendered_notes)
            + "\n"
            + "请在本轮显式规避上述失败模式，优先采用与其相反的修复策略。\n"
        )

    def _extract_swe_regen_failure_note(
        self,
        run_task_result: Any,
        summary_feedback: str,
        detailed_feedback: str,
        cargo_check_output: str,
    ) -> str:
        note_lines: List[str] = []

        if summary_feedback:
            note_lines.append("本轮主要失败摘要:")
            note_lines.append(self._clip_text(summary_feedback, 280))

        if detailed_feedback:
            detail = self._strip_cargo_check_raw(detailed_feedback)
            if detail:
                note_lines.append("关键诊断细节:")
                note_lines.append(self._clip_text(detail, 360))

        if isinstance(run_task_result, dict):
            final_response = (run_task_result.get("final_response", "") or "").strip()
            if final_response:
                note_lines.append("CC-MINI Agent 失败分析:")
                note_lines.append(self._clip_text(final_response, 420))

        if cargo_check_output:
            note_lines.append("CC-MINI 复验关键输出:")
            note_lines.append(self._clip_text(cargo_check_output, 360))

        note = "\n".join(note_lines).strip()
        return self._clip_text(note, self.swe_regen_assist_note_max_chars)

    def _refresh_verify_failure_sandbox(
        self,
        test_source_name: str,
        source_name: str,
        func_name: str,
        include_files: List[str],
        archive: Dict[str, Dict[str, str]],
    ):
        refresh_scope = self._collect_archive_verify_sources(archive, source_name, include_files)
        if not refresh_scope:
            refresh_scope = [source_name]

        module_sources, _ = self._build_module_sources(archive, refresh_scope)
        prev_cache_enabled = bool(getattr(self.verifier, "verify_cache_enabled", False))
        prev_keep_sandbox = bool(getattr(self.verifier, "keep_sandbox_on_failure", False))

        try:
            # CC-MINI assist requires a real sandbox path. Bypass verify cache for one refresh.
            self.verifier.verify_cache_enabled = False
            self.verifier.keep_sandbox_on_failure = True
            refreshed = self.verifier.verify_modules(
                module_sources=module_sources,
                crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_swe_refresh",
            )
        except Exception as exc:
            self.logger.info(
                f"[CC-MINI-SANDBOX-REFRESH-FAIL] {test_source_name}:{func_name} err={exc}"
            )
            return None
        finally:
            self.verifier.verify_cache_enabled = prev_cache_enabled
            self.verifier.keep_sandbox_on_failure = prev_keep_sandbox

        self.logger.info(
            f"[CC-MINI-SANDBOX-REFRESH] {test_source_name}:{func_name} success={refreshed.success} diagnostics={len(refreshed.diagnostics)} cache_hit={int(getattr(refreshed, 'cache_hit', False))} sandbox={refreshed.sandbox_dir}"
        )
        return refreshed

    def _materialize_swe_failure_sandbox(
        self,
        test_source_name: str,
        source_name: str,
        func_name: str,
        include_files: List[str],
        archive: Dict[str, Dict[str, str]],
    ) -> str:
        """Create the Cargo sandbox used for CC-MINI failure investigation."""
        scope = self._collect_archive_verify_sources(archive, source_name, include_files)
        if not scope:
            scope = [source_name]

        module_sources, _ = self._build_module_sources(archive, scope)
        base_tmp_dir = os.path.abspath(getattr(self.verifier, "base_tmp_dir", "") or tempfile.gettempdir())
        os.makedirs(base_tmp_dir, exist_ok=True)

        sandbox_dir = tempfile.mkdtemp(prefix="cargo_verify_swe_", dir=base_tmp_dir)
        src_dir = os.path.join(sandbox_dir, "src")
        os.makedirs(src_dir, exist_ok=True)

        try:
            if hasattr(self.verifier, "_write_cargo_project"):
                self.verifier._write_cargo_project(
                    crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_swe_materialized",
                    src_dir=src_dir,
                    module_sources=module_sources,
                )
            else:
                cargo_toml = os.path.join(sandbox_dir, "Cargo.toml")
                with open(cargo_toml, "w", encoding="utf-8") as f:
                    f.write(
                        "[package]\n"
                        "name = \"translation_sandbox\"\n"
                        "version = \"0.1.0\"\n"
                        "edition = \"2021\"\n\n"
                        "[lib]\n"
                        "path = \"src/lib.rs\"\n\n"
                        "[dependencies]\n"
                        "libc = \"0.2\"\n"
                    )

                lib_lines = ["#![allow(warnings)]"]
                for module_name in sorted(module_sources.keys()):
                    lib_lines.append(f"pub mod {module_name};")
                    module_path = os.path.join(src_dir, f"{module_name}.rs")
                    with open(module_path, "w", encoding="utf-8") as mf:
                        mf.write((module_sources[module_name] or "") + "\n")
                with open(os.path.join(src_dir, "lib.rs"), "w", encoding="utf-8") as f:
                    f.write("\n".join(lib_lines) + "\n")
        except Exception:
            try:
                import shutil

                shutil.rmtree(sandbox_dir, ignore_errors=True)
            except Exception:
                pass
            raise

        self.logger.info(
            f"[CC-MINI-SANDBOX-MATERIALIZED] {test_source_name}:{func_name} sandbox={sandbox_dir} scope={len(scope)}"
        )
        return sandbox_dir

    def _attempt_cc_mini_agent_regen_assist(
        self,
        test_source_name: str,
        source_name: str,
        func_name: str,
        include_files: List[str],
        base_archive: Dict[str, Dict[str, str]],
        verify_result,
        summary_feedback: str,
        detailed_feedback: str,
    ) -> Tuple[Optional[Dict[str, Dict[str, str]]], str, str]:
        """Ask CC-MINI to assist a regeneration attempt without taking full ownership."""
        sandbox_dir = getattr(verify_result, "sandbox_dir", "")
        if not sandbox_dir or not os.path.isdir(sandbox_dir):
            refreshed = self._refresh_verify_failure_sandbox(
                test_source_name=test_source_name,
                source_name=source_name,
                func_name=func_name,
                include_files=include_files,
                archive=base_archive,
            )
            if refreshed is not None:
                verify_result = refreshed
                sandbox_dir = getattr(verify_result, "sandbox_dir", "")
                if verify_result.success:
                    return None, "skip: sandbox 刷新后已通过，无需 assist", ""
            if not sandbox_dir or not os.path.isdir(sandbox_dir):
                try:
                    sandbox_dir = self._materialize_swe_failure_sandbox(
                        test_source_name=test_source_name,
                        source_name=source_name,
                        func_name=func_name,
                        include_files=include_files,
                        archive=base_archive,
                    )
                except Exception as exc:
                    return None, f"skip: 失败 sandbox 不可用（cache-hit 或目录已清理，且物化失败: {exc}）", ""

        agent = self._get_cc_mini_agent_instance(sandbox_dir)
        if agent is None:
            return None, "skip: CC-MINI Agent 不可用", ""

        module_name = normalize_rust_module_name(source_name)
        module_path = os.path.join(sandbox_dir, "src", f"{module_name}.rs")
        if not os.path.exists(module_path):
            return None, f"skip: sandbox 缺少模块文件 {module_name}.rs", ""

        compile_cmd = "cargo check --tests --quiet"
        context_feedback = self._compose_model_compile_feedback(summary_feedback, detailed_feedback)
        prompt_diagnostic_codes = self._collect_swe_prompt_diagnostic_codes(
            summary_feedback=summary_feedback,
            detailed_feedback=detailed_feedback,
            verify_result=verify_result,
        )
        # strategy_notes = self._build_swe_strategy_notes(
        #     source_name=source_name,
        #     func_name=func_name,
        #     module_name=module_name,
        #     diagnostic_codes=prompt_diagnostic_codes,
        #     compile_cmd=compile_cmd,
        # )
        task_description = "".join(
            [
                "请在当前 sandbox 中执行修复尝试：对代码库中的Bug进行编辑修复并执行复验。",
                "若复验成功则停止并调用finish；若失败，且无法修复，转而总结失败根因。\n",
                (f"关键诊断码：{', '.join(prompt_diagnostic_codes)}\n" if prompt_diagnostic_codes else ""),
                f"复验命令：{compile_cmd}\n",
                "执行协议（必须严格按顺序）：\n",
                f"1) 先调查失败原因，使用replace工具编辑修复，再直接执行且仅执行验收命令 `{compile_cmd}`（原样，不包装）。\n",
                "2) 只有当该命令返回码为 0，且编译无报错输出，才允许调用 finish。\n",
                "提示：验收成功后可以通过调用 finish 结束任务。\n",
                "验收命令必须原样直接执行，禁止使用 `|`、`head`、`tail`、`&&`、`||`、`;` 等包装该命令；",
                "如需查看输出，请在单独命令中查看，不要把截断输出的命令当作验收。\n",
                "严禁在未执行验收命令、或验收命令未确认成功前输出最终回复。\n",
                "最终回复必须包含以下头部字段（逐行给出）：\n",
                "[FINAL_STATUS] PASS 或 FAIL\n",
                f"[CHECK_CMD] {compile_cmd}\n",
                "[CHECK_RESULT] returncode=<数字>\n",
                "失败时请在最终回复中给出两段：\n",
                "[FAIL_SUMMARY]\n- 本轮未通过的关键原因\n",
                "[AVOID_NEXT_REGEN]\n- 下一轮生成的代码要避免的错误模式\n",
            ]
        )

        run_task_summary = ""
        run_task_result: Any = {}
        try:
            run_task_result = agent.run_task(
                task_description,
                acceptance_criteria=[
                    f"必须直接执行 `{compile_cmd}`（原样，无管道/无包装），并且该次执行 returncode=0 且输出无编译错误才能视为 PASS",
                    "未执行验收命令或 returncode!=0 时，最终状态必须为 [FINAL_STATUS] FAIL，且不得宣称通过",
                    "若失败，输出 [FAIL_SUMMARY] 与 [AVOID_NEXT_REGEN]",
                ],
            )
            run_task_summary = self._summarize_cc_mini_agent_result(run_task_result)
        except Exception as exc:
            return None, f"run_task 异常: {exc}", ""

        acceptance_ok, acceptance_msg = self._validate_swe_acceptance_command(
            run_task_result,
            compile_cmd,
        )
        if not acceptance_ok:
            self.logger.info(
                f"[CC-MINI-ACCEPT-CMD-INVALID] {test_source_name}:{func_name} {acceptance_msg}"
            )
            protocol_output = "(not executed)"
            try:
                protocol_rerun = agent.toolset.run_command(compile_cmd)
                protocol_output = self._summarize_tool_output(protocol_rerun, max_lines=40)
            except Exception as exc:
                protocol_output = f"复验命令执行失败: {exc}"
            note = self._extract_swe_regen_failure_note(
                run_task_result=run_task_result,
                summary_feedback=summary_feedback,
                detailed_feedback=detailed_feedback,
                cargo_check_output=protocol_output,
            )
            msg = "CC-MINI Agent 未按验收协议执行（可能提前 finish）"
            if run_task_summary:
                msg += f"\n[CC-MINI run]\n{run_task_summary}"
            msg += f"\n[CC-MINI acceptance]\n{acceptance_msg}"
            msg += f"\n[CC-MINI cargo check]\n{protocol_output}"
            return None, msg, note

        try:
            rerun = agent.toolset.run_command(compile_cmd)
        except Exception as exc:
            return None, f"复验命令执行失败: {exc}", ""

        rerun_returncode_ok = int((rerun or {}).get("returncode", 1)) == 0
        rerun_clean_output = not self._cargo_output_has_error_markers(rerun)
        rerun_ok = rerun_returncode_ok and rerun_clean_output
        rerun_output = self._summarize_tool_output(rerun, max_lines=40)

        if not rerun_ok:
            note = self._extract_swe_regen_failure_note(
                run_task_result=run_task_result,
                summary_feedback=summary_feedback,
                detailed_feedback=detailed_feedback,
                cargo_check_output=rerun_output,
            )
            msg = "单次 CC-MINI 修复未通过"
            if run_task_summary:
                msg += f"\n[CC-MINI run]\n{run_task_summary}"
            if not acceptance_ok:
                msg += f"\n[CC-MINI acceptance]\n{acceptance_msg}"
            msg += f"\n[CC-MINI cargo check]\n{rerun_output}"
            return None, msg, note

        self._update_dependency_overrides_from_cargo_toml(
            os.path.join(sandbox_dir, "Cargo.toml"),
            log_label=f"swe-regen:{test_source_name}:{func_name}",
        )

        try:
            with open(module_path, "r", encoding="utf-8") as f:
                fixed_module_text = f.read()
        except Exception as exc:
            return None, f"读取修复后的模块失败: {exc}", ""

        rebuilt_target_bucket, rebuilt_target_error = self._rebuild_bucket_from_module_text(
            source_name,
            fixed_module_text,
            required_func=func_name,
            previous_bucket=base_archive.get(source_name, {}),
        )
        if rebuilt_target_error:
            return None, f"回灌失败: {rebuilt_target_error}", ""

        self._update_dependency_overrides_from_cargo_toml(
            os.path.join(sandbox_dir, "Cargo.toml"),
            log_label=f"swe-fallback:{test_source_name}:{func_name}",
        )

        candidate_results = copy.deepcopy(base_archive)
        candidate_results[source_name] = rebuilt_target_bucket

        for src in include_files:
            if src == source_name:
                continue
            src_module_name = normalize_rust_module_name(src)
            src_module_path = os.path.join(sandbox_dir, "src", f"{src_module_name}.rs")
            if not os.path.exists(src_module_path):
                continue
            try:
                with open(src_module_path, "r", encoding="utf-8") as f:
                    src_module_text = f.read()
            except Exception:
                continue
            rebuilt_bucket, rebuilt_error = self._rebuild_bucket_from_module_text(
                src,
                src_module_text,
                previous_bucket=base_archive.get(src, {}),
            )
            if rebuilt_error or not rebuilt_bucket:
                continue
            candidate_results[src] = rebuilt_bucket

        module_sources, _ = self._build_module_sources(candidate_results, include_files)
        verify_after = self.verifier.verify_modules(
            module_sources=module_sources,
            crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_swe_regen_assist",
        )
        if not verify_after.success:
            verify_after_detail = self._format_verify_diagnostics_for_debug(
                verify_after,
                focus_modules={normalize_rust_module_name(source_name)},
                max_items=10,
                max_rendered_chars=300,
            )
            msg = (
                "单次 CC-MINI 修复在回灌后验证失败: "
                + verify_after.summarize_for_llm(
                    max_items=10,
                    focus_modules={normalize_rust_module_name(source_name)},
                )
            )
            if verify_after_detail:
                msg += f"\n{verify_after_detail}"
            return None, msg, ""

        success_msg = "单次 CC-MINI 修复通过并已回灌"
        if run_task_summary:
            success_msg += f"\n[CC-MINI run]\n{run_task_summary}"
        return candidate_results, success_msg, ""

    def _attempt_cc_mini_agent_fallback(
        self,
        test_source_name: str,
        source_name: str,
        func_name: str,
        include_files: List[str],
        base_archive: Dict[str, Dict[str, str]],
        verify_result,
    ) -> Tuple[Optional[Dict[str, Dict[str, str]]], str]:
        """Run the full CC-MINI fallback path and merge accepted repairs."""
        sandbox_dir = getattr(verify_result, "sandbox_dir", "")
        if not sandbox_dir or not os.path.isdir(sandbox_dir):
            refreshed = self._refresh_verify_failure_sandbox(
                test_source_name=test_source_name,
                source_name=source_name,
                func_name=func_name,
                include_files=include_files,
                archive=base_archive,
            )
            if refreshed is not None:
                verify_result = refreshed
                sandbox_dir = getattr(verify_result, "sandbox_dir", "")
                if verify_result.success:
                    return None, "fallback 前刷新校验已通过，无需 fallback"
            if not sandbox_dir or not os.path.isdir(sandbox_dir):
                try:
                    sandbox_dir = self._materialize_swe_failure_sandbox(
                        test_source_name=test_source_name,
                        source_name=source_name,
                        func_name=func_name,
                        include_files=include_files,
                        archive=base_archive,
                    )
                except Exception as exc:
                    return (
                        None,
                        f"fallback 无法获取失败 sandbox（cache-hit 或目录已清理，且物化失败: {exc}）",
                    )

        agent = self._get_cc_mini_agent_instance(sandbox_dir)
        if agent is None:
            return None, "CC-MINI Agent 不可用"

        module_name = normalize_rust_module_name(source_name)
        module_path = os.path.join(sandbox_dir, "src", f"{module_name}.rs")
        if not os.path.exists(module_path):
            return None, f"sandbox 缺少模块文件: {module_name}.rs"

        compile_cmd = "cargo check --tests --quiet"
        prompt_diagnostic_codes = self._collect_swe_prompt_diagnostic_codes(
            summary_feedback="",
            detailed_feedback="",
            verify_result=verify_result,
        )
        strategy_notes = self._build_swe_strategy_notes(
            source_name=source_name,
            func_name=func_name,
            module_name=module_name,
            diagnostic_codes=prompt_diagnostic_codes,
            compile_cmd=compile_cmd,
        )
        task_description = "".join(
            [
                "cargo check 失败，请修复并确保编译通过。",
                "优先修改目标模块；若根因在共享定义，可扩展到相关文件联动修复。不要删除函数。",
                f"优先修复目标函数：{func_name}，并保持函数名不变。\n",
                f"出错模块：src/{module_name}.rs\n",
                (f"关键诊断码：{', '.join(prompt_diagnostic_codes)}\n" if prompt_diagnostic_codes else ""),
                f"复验命令：{compile_cmd}\n",
                "执行协议（必须严格按顺序）：\n",
                f"1) 先编辑修复，再直接执行且仅执行验收命令 `{compile_cmd}`（原样，不包装）。\n",
                "2) 只有当该命令返回码为 0 且无编译错误输出，才允许调用 finish。\n",
                "3) 若返回码非 0 或输出仍有编译错误且暂时无法修复，可调用 finish，但必须先执行过验收命令并报告失败。\n",
                "验收命令必须原样直接执行，禁止使用 `|`、`head`、`tail`、`&&`、`||`、`;` 等包装该命令；",
                "如需查看输出，请在单独命令中查看，不要把截断输出的命令当作验收。\n",
                "严禁在未执行验收命令、或验收命令未成功前直接 finish。\n",
                "最终回复必须包含以下头部字段（逐行给出）：\n",
                "[FINAL_STATUS] PASS 或 FAIL\n",
                f"[CHECK_CMD] {compile_cmd}\n",
                "[CHECK_RESULT] returncode=<数字>\n",
                "失败时额外输出：\n",
                "[FAIL_SUMMARY]\n- 本轮未通过的关键原因",
            ]
        )

        self.logger.info(
            f"[CC-MINI-FALLBACK-TRY] {test_source_name}:{func_name} sandbox={sandbox_dir}"
        )

        run_task_summary = ""
        run_task_result: Any = {}
        try:
            run_task_result = agent.run_task(
                task_description,
                acceptance_criteria=[
                    f"必须直接执行 `{compile_cmd}`（原样，无管道/无包装），并且该次执行 returncode=0 且输出无编译错误才能视为 PASS",
                    "未执行验收命令或 returncode!=0 时，最终状态必须为 [FINAL_STATUS] FAIL，且不得宣称通过",
                    "若失败，输出 [FAIL_SUMMARY]",
                ],
                extra_notes=strategy_notes,
            )
            run_task_summary = self._summarize_cc_mini_agent_result(run_task_result)
            if run_task_summary:
                self.logger.info(
                    f"[CC-MINI-FALLBACK-RUN] {test_source_name}:{func_name}\n{run_task_summary}"
                )
        except Exception as exc:
            return None, f"run_task 异常: {exc}"

        acceptance_ok, acceptance_msg = self._validate_swe_acceptance_command(
            run_task_result,
            compile_cmd,
        )
        if not acceptance_ok:
            self.logger.info(
                f"[CC-MINI-ACCEPT-CMD-INVALID] {test_source_name}:{func_name} {acceptance_msg}"
            )
            protocol_output = "(not executed)"
            try:
                protocol_rerun = agent.toolset.run_command(compile_cmd)
                protocol_output = self._summarize_tool_output(protocol_rerun, max_lines=40)
            except Exception as exc:
                protocol_output = f"复验命令执行失败: {exc}"
            msg = "CC-MINI Agent 未按验收协议执行（可能提前 finish）"
            if run_task_summary:
                msg += f"\n[CC-MINI run]\n{run_task_summary}"
            msg += f"\n[CC-MINI acceptance]\n{acceptance_msg}"
            msg += f"\n[CC-MINI cargo check]\n{protocol_output}"
            return None, msg

        try:
            rerun = agent.toolset.run_command(compile_cmd)
        except Exception as exc:
            return None, f"复验命令执行失败: {exc}"

        rerun_returncode_ok = int((rerun or {}).get("returncode", 1)) == 0
        rerun_clean_output = not self._cargo_output_has_error_markers(rerun)
        if not (rerun_returncode_ok and rerun_clean_output):
            output = self._summarize_tool_output(rerun, max_lines=40)
            self.logger.info(
                f"[CC-MINI-FALLBACK-CHECK-FAIL] {test_source_name}:{func_name}\n{output}"
            )
            msg = "CC-MINI Agent 修复后仍未通过:"
            if run_task_summary:
                msg += f"\n[CC-MINI run]\n{run_task_summary}"
            if not acceptance_ok:
                msg += f"\n[CC-MINI acceptance]\n{acceptance_msg}"
            msg += f"\n[CC-MINI cargo check]\n{output}"
            return None, msg

        try:
            with open(module_path, "r", encoding="utf-8") as f:
                fixed_module_text = f.read()
        except Exception as exc:
            return None, f"读取修复后的模块失败: {exc}"

        rebuilt_target_bucket, rebuilt_target_error = self._rebuild_bucket_from_module_text(
            source_name,
            fixed_module_text,
            required_func=func_name,
            previous_bucket=base_archive.get(source_name, {}),
        )
        if rebuilt_target_error:
            return None, f"回灌失败: {rebuilt_target_error}"

        candidate_results = copy.deepcopy(base_archive)
        candidate_results[source_name] = rebuilt_target_bucket

        # Promote cross-module fixes produced by CC-MINI fallback for modules in current include scope.
        for src in include_files:
            if src == source_name:
                continue
            src_module_name = normalize_rust_module_name(src)
            src_module_path = os.path.join(sandbox_dir, "src", f"{src_module_name}.rs")
            if not os.path.exists(src_module_path):
                continue
            try:
                with open(src_module_path, "r", encoding="utf-8") as f:
                    src_module_text = f.read()
            except Exception:
                continue
            rebuilt_bucket, rebuilt_error = self._rebuild_bucket_from_module_text(
                src,
                src_module_text,
                previous_bucket=base_archive.get(src, {}),
            )
            if rebuilt_error or not rebuilt_bucket:
                continue
            candidate_results[src] = rebuilt_bucket

        module_sources, _ = self._build_module_sources(candidate_results, include_files)
        verify_after = self.verifier.verify_modules(
            module_sources=module_sources,
            crate_name=f"verify_{normalize_rust_module_name(test_source_name)}_swe",
        )
        if not verify_after.success:
            verify_after_detail = self._format_verify_diagnostics_for_debug(
                verify_after,
                focus_modules={normalize_rust_module_name(source_name)},
                max_items=10,
                max_rendered_chars=300,
            )
            return (
                None,
                "回灌后验证失败: "
                + verify_after.summarize_for_llm(
                    max_items=10,
                    focus_modules={normalize_rust_module_name(source_name)},
                )
                + (f"\n{verify_after_detail}" if verify_after_detail else ""),
            )

        success_msg = "CC-MINI Agent 修复并通过验证"
        if run_task_summary:
            success_msg += f"\n[CC-MINI run]\n{run_task_summary}"
        return candidate_results, success_msg

    def _rebuild_bucket_from_module_text(
        self,
        source_name: str,
        module_text: str,
        required_func: str = "",
        previous_bucket: Optional[Dict[str, str]] = None,
    ) -> Tuple[Dict[str, str], str]:
        split = split_rust_code_structural(module_text, tmp_dir=None)
        record_ast_split_result(split.ast_ok, split.fallback_used)
        if split.fallback_used:
            self.logger.info(
                f"[AST-SPLIT-FALLBACK] {source_name}:{required_func or '*'} {split.diagnostic}"
            )
        non_function_content = split.non_function_content
        function_content_dict = split.function_content_dict

        rebuilt_bucket: Dict[str, str] = {}
        if non_function_content.strip():
            if self._is_test_source(source_name):
                if split.ast_ok:
                    rebuilt_extra = non_function_content.strip()
                else:
                    rebuilt_extra = self._sanitize_non_function_content(non_function_content)
            else:
                rebuilt_extra = dedupe_non_function_content(non_function_content).strip()

            if rebuilt_extra:
                rebuilt_extra = self._dedupe_use_statements(rebuilt_extra).strip()
                rebuilt_extra, restored_owned = self._preserve_owned_declaration_blocks(
                    source_name,
                    rebuilt_extra,
                    (previous_bucket or {}).get("extra", ""),
                )
                if restored_owned:
                    self.logger.info(
                        f"[OWNER-DECL-RESTORE-REBUILD] {source_name} restored={','.join(restored_owned[:8])}"
                    )
                rebuilt_bucket["extra"] = rebuilt_extra if rebuilt_extra.endswith("\n") else rebuilt_extra + "\n"

        for name, code in function_content_dict.items():
            trimmed = self._trim_to_function_definition(code)
            if not trimmed or not is_rust_snippet_brace_balanced(trimmed):
                continue
            normalized_code = trimmed
            if not self._is_test_source(source_name):
                normalized_code = self._ensure_public_function(normalized_code)
            rebuilt_bucket[name] = normalized_code if normalized_code.endswith("\n") else normalized_code + "\n"

        if required_func and required_func not in rebuilt_bucket:
            return {}, f"修复结果中缺少目标函数 {required_func}"

        restored_functions: List[str] = []
        previous_bucket = previous_bucket or {}
        rebuilt_rust_fn_names = {
            self._extract_rust_function_name_from_code(code)
            for name, code in rebuilt_bucket.items()
            if name != "extra" and (code or "").strip()
        }
        rebuilt_rust_fn_names.discard("")
        for prev_name, prev_code in previous_bucket.items():
            if prev_name == "extra":
                continue
            if prev_name in rebuilt_bucket:
                continue
            if not (prev_code or "").strip() or not is_rust_snippet_brace_balanced(prev_code):
                continue
            prev_rust_fn_name = self._extract_rust_function_name_from_code(prev_code)
            if prev_rust_fn_name and prev_rust_fn_name in rebuilt_rust_fn_names:
                self.logger.info(
                    f"[REBUILD-PRESERVE-SKIP-DUP] {source_name} skipped={prev_name} rust_fn={prev_rust_fn_name}"
                )
                continue
            rebuilt_bucket[prev_name] = prev_code if prev_code.endswith("\n") else prev_code + "\n"
            if prev_rust_fn_name:
                rebuilt_rust_fn_names.add(prev_rust_fn_name)
            restored_functions.append(prev_name)

        if restored_functions:
            self.logger.info(
                f"[REBUILD-PRESERVE-FN] {source_name} restored={','.join(restored_functions[:10])}"
            )

        if not rebuilt_bucket:
            return {}, "修复结果未解析到有效模块内容"

        return rebuilt_bucket, ""
