import json
import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CargoDiagnostic:
    level: str
    message: str
    code: str
    file: str
    module: str
    line: int
    column: int
    rendered: str


@dataclass
class CargoCheckResult:
    success: bool
    diagnostics: List[CargoDiagnostic]
    returncode: int
    raw_output: str
    sandbox_dir: str
    cache_hit: bool = False

    def summarize_for_llm(self, max_items: int = 20, focus_modules: Optional[set] = None) -> str:
        if not self.diagnostics:
            return "No diagnostics."

        lines = []
        kept = 0
        for diag in self.diagnostics:
            if focus_modules and diag.module and diag.module not in focus_modules:
                continue
            lines.append(
                f"[{diag.level}] {diag.code} {diag.module}:{diag.line}:{diag.column} {diag.message}".strip()
            )
            kept += 1
            if kept >= max_items:
                break

        if not lines:
            lines = [
                f"[{diag.level}] {diag.code} {diag.module}:{diag.line}:{diag.column} {diag.message}".strip()
                for diag in self.diagnostics[:max_items]
            ]

        return "\n".join(lines)


class CargoVerifier:
    """Builds a sandbox Cargo module tree and runs cargo check with JSON diagnostics."""

    def __init__(
        self,
        base_tmp_dir: str,
        keep_sandbox_on_failure: bool = False,
        verify_timeout_seconds: int = 120,
        verify_cache_enabled: bool = True,
    ):
        self.base_tmp_dir = os.path.abspath(base_tmp_dir)
        self.keep_sandbox_on_failure = keep_sandbox_on_failure
        self.verify_timeout_seconds = max(1, int(verify_timeout_seconds))
        self.verify_cache_enabled = bool(verify_cache_enabled)
        self._verify_cache: Dict[str, CargoCheckResult] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.dependency_overrides: Dict[str, str] = {}
        self.shared_target_dir = os.path.join(self.base_tmp_dir, "cargo_target_shared")
        os.makedirs(self.base_tmp_dir, exist_ok=True)
        os.makedirs(self.shared_target_dir, exist_ok=True)

    @staticmethod
    def _clone_result(result: CargoCheckResult, cache_hit: bool) -> CargoCheckResult:
        diagnostics = [
            CargoDiagnostic(
                level=d.level,
                message=d.message,
                code=d.code,
                file=d.file,
                module=d.module,
                line=d.line,
                column=d.column,
                rendered=d.rendered,
            )
            for d in (result.diagnostics or [])
        ]
        sandbox_dir = "[cache-hit]" if cache_hit else result.sandbox_dir
        return CargoCheckResult(
            success=result.success,
            diagnostics=diagnostics,
            returncode=result.returncode,
            raw_output=result.raw_output,
            sandbox_dir=sandbox_dir,
            cache_hit=cache_hit,
        )

    @staticmethod
    def _is_timeout_result(result: Optional[CargoCheckResult]) -> bool:
        if result is None:
            return False
        if int(getattr(result, "returncode", 0) or 0) == 124:
            return True
        for diag in getattr(result, "diagnostics", []) or []:
            if (getattr(diag, "code", "") or "").strip().upper() == "TIMEOUT":
                return True
        return False

    def _make_cache_key(self, module_sources: Dict[str, str]) -> str:
        hasher = hashlib.sha256()
        hasher.update(f"verify_timeout_seconds={self.verify_timeout_seconds}\n".encode("utf-8"))
        for module_name in sorted(module_sources.keys()):
            body = module_sources[module_name] or ""
            hasher.update(f"module::{module_name}\n".encode("utf-8"))
            hasher.update(body.encode("utf-8", errors="ignore"))
            hasher.update(b"\n---\n")
        return hasher.hexdigest()

    def verify_modules(self, module_sources: Dict[str, str], crate_name: str = "translation_sandbox") -> CargoCheckResult:
        cache_key = ""
        if self.verify_cache_enabled:
            cache_key = self._make_cache_key(module_sources)
            cached = self._verify_cache.get(cache_key)
            if cached is not None:
                # Never reuse cached timeout results; force a real verify run.
                if self._is_timeout_result(cached):
                    del self._verify_cache[cache_key]
                else:
                    self.cache_hits += 1
                    return self._clone_result(cached, cache_hit=True)
            self.cache_misses += 1

        sandbox_dir = tempfile.mkdtemp(prefix="cargo_verify_", dir=self.base_tmp_dir)
        src_dir = os.path.join(sandbox_dir, "src")
        os.makedirs(src_dir, exist_ok=True)

        self._write_cargo_project(crate_name=crate_name, src_dir=src_dir, module_sources=module_sources)

        cmd = [
            "cargo",
            "check",
            "--message-format=json",
            "--quiet",
        ]

        try:
            env = os.environ.copy()
            env["CARGO_TARGET_DIR"] = self.shared_target_dir

            proc = subprocess.run(
                cmd,
                cwd=sandbox_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=self.verify_timeout_seconds,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            timeout_output = "\n".join(
                [
                    (exc.stdout or "").strip(),
                    (exc.stderr or "").strip(),
                ]
            ).strip()
            diagnostics = [
                CargoDiagnostic(
                    level="error",
                    message=f"cargo check timed out after {self.verify_timeout_seconds}s",
                    code="TIMEOUT",
                    file="",
                    module="",
                    line=0,
                    column=0,
                    rendered=f"cargo check timed out after {self.verify_timeout_seconds}s",
                )
            ]
            result = CargoCheckResult(
                success=False,
                diagnostics=diagnostics,
                returncode=124,
                raw_output=timeout_output,
                sandbox_dir=sandbox_dir,
                cache_hit=False,
            )
            if not self.keep_sandbox_on_failure:
                shutil.rmtree(sandbox_dir, ignore_errors=True)
            return result

        diagnostics = self._parse_diagnostics(proc.stdout, proc.stderr)
        success = proc.returncode == 0 and not any(d.level == "error" for d in diagnostics)

        raw_output = "\n".join([proc.stdout.strip(), proc.stderr.strip()]).strip()
        result = CargoCheckResult(
            success=success,
            diagnostics=diagnostics,
            returncode=proc.returncode,
            raw_output=raw_output,
            sandbox_dir=sandbox_dir,
            cache_hit=False,
        )

        if self.verify_cache_enabled and cache_key and not self._is_timeout_result(result):
            self._verify_cache[cache_key] = self._clone_result(result, cache_hit=False)

        if success or not self.keep_sandbox_on_failure:
            shutil.rmtree(sandbox_dir, ignore_errors=True)

        return result

    def _render_dependency_section(self) -> str:
        deps: Dict[str, str] = {}
        for name, value in (self.dependency_overrides or {}).items():
            key = str(name or "").strip()
            if not key:
                continue
            deps[key] = str(value or "").strip() or "\"*\""

        if not deps:
            return ""

        lines = ["[dependencies]"]
        for dep_name in sorted(deps.keys()):
            lines.append(f"{dep_name} = {deps[dep_name]}")
        return "\n".join(lines) + "\n"

    def _write_cargo_project(self, crate_name: str, src_dir: str, module_sources: Dict[str, str]) -> None:
        cargo_toml_path = os.path.join(os.path.dirname(src_dir), "Cargo.toml")
        with open(cargo_toml_path, "w", encoding="utf-8") as f:
            f.write(
                "[package]\n"
                f"name = \"{crate_name}\"\n"
                "version = \"0.1.0\"\n"
                "edition = \"2021\"\n\n"
                "[lib]\n"
                "path = \"src/lib.rs\"\n\n"
                + self._render_dependency_section()
            )

        module_lines = ["#![allow(warnings)]"]
        for module_name in sorted(module_sources.keys()):
            module_lines.append(f"pub mod {module_name};")
            module_path = os.path.join(src_dir, f"{module_name}.rs")
            with open(module_path, "w", encoding="utf-8") as mf:
                mf.write((module_sources[module_name] or "") + "\n")

        lib_rs_path = os.path.join(src_dir, "lib.rs")
        with open(lib_rs_path, "w", encoding="utf-8") as f:
            f.write("\n".join(module_lines) + "\n")

    def _parse_diagnostics(self, stdout: str, stderr: str) -> List[CargoDiagnostic]:
        diagnostics: List[CargoDiagnostic] = []
        for stream in (stdout, stderr):
            for line in stream.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if msg.get("reason") != "compiler-message":
                    continue

                data = msg.get("message", {})
                level = data.get("level", "unknown")
                if level not in {"error", "warning"}:
                    continue

                code = (data.get("code") or {}).get("code", "")
                message = data.get("message", "")
                rendered = data.get("rendered", "") or message

                spans = data.get("spans") or []
                primary = None
                for span in spans:
                    if span.get("is_primary"):
                        primary = span
                        break
                if primary is None and spans:
                    primary = spans[0]

                file_name = ""
                line_start = 0
                column_start = 0
                module = ""
                if primary:
                    file_name = primary.get("file_name", "")
                    line_start = int(primary.get("line_start", 0) or 0)
                    column_start = int(primary.get("column_start", 0) or 0)
                    base = os.path.basename(file_name)
                    module = os.path.splitext(base)[0]

                diagnostics.append(
                    CargoDiagnostic(
                        level=level,
                        message=message,
                        code=code,
                        file=file_name,
                        module=module,
                        line=line_start,
                        column=column_start,
                        rendered=rendered,
                    )
                )

        return diagnostics
