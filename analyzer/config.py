from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Union

import yaml
CONFIG_ENV_VAR = "ANALYZER_CONFIG_PATH"
_ANALYZER_DIR = Path(__file__).resolve().parent
_DEFAULT_CONFIG_PATH = (_ANALYZER_DIR.parent / "analyzer_config.yaml").resolve()


class AnalyzerConfigError(RuntimeError):
    """Raised when the analyzer configuration cannot be loaded or is invalid."""


@lru_cache(maxsize=1)
def _get_config_path() -> Path:
    env_value = os.environ.get(CONFIG_ENV_VAR)
    if env_value:
        path = Path(env_value)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
    else:
        path = _DEFAULT_CONFIG_PATH
    return path


def get_config_path() -> Path:
    return _get_config_path()


@lru_cache(maxsize=1)
def _load_config_dict() -> Dict[str, Any]:
    config_path = _get_config_path()
    if not config_path.exists():
        raise AnalyzerConfigError(f"配置文件未找到: {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:  # type: ignore[attr-defined]
        raise AnalyzerConfigError(f"配置文件解析失败: {exc}") from exc

    if not isinstance(data, dict):
        raise AnalyzerConfigError("配置文件根结点必须是映射对象")
    return data

@lru_cache(maxsize=1)
def load_rust_output_dir() -> Path:
    config_path = _get_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        config_data = yaml.safe_load(fh) or {}

    rust_output_value = config_data.get("rust_output")
    if not rust_output_value:
        raise ValueError("配置文件缺少 rust_output 字段")

    rust_output_path = Path(rust_output_value)
    if not rust_output_path.is_absolute():
        rust_output_path = (config_path.parent / rust_output_path).resolve()

    return rust_output_path

@lru_cache(maxsize=1)
def get_project_root() -> Path:
    data = _load_config_dict()
    root_value = data.get("project_root")
    if not root_value:
        raise AnalyzerConfigError("配置文件缺少 project_root")

    root_path = Path(root_value)
    if not root_path.is_absolute():
        root_path = (_get_config_path().parent / root_path).resolve()
    return root_path


@lru_cache(maxsize=1)
def get_output_dir() -> Path:
    data = _load_config_dict()
    output_value = data.get("output_root") or data.get("output_dir") or data.get("output_path")

    if output_value:
        expanded = os.path.expanduser(str(output_value))
        expanded = os.path.expandvars(expanded)
        output_path = Path(expanded)
        if not output_path.is_absolute():
            output_path = (_get_config_path().parent / output_path).resolve()
    else:
        output_path = (_ANALYZER_DIR / "output").resolve()

    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def resolve_output_path(*path_parts: Union[str, Path]) -> Path:
    output_dir = get_output_dir()
    parts: Iterable[Union[str, Path]] = path_parts or ()
    resolved = output_dir.joinpath(*(Path(part) for part in parts))
    return resolved.resolve()


def to_absolute_path(path_like: Union[str, Path]) -> Path:
    path_obj = Path(path_like)
    if path_obj.is_absolute():
        return path_obj

    project_root = get_project_root()
    candidate = (project_root / path_obj).resolve()
    if candidate.exists():
        return candidate

    analyzer_relative = (_ANALYZER_DIR / path_obj).resolve()
    if analyzer_relative.exists():
        return analyzer_relative

    workspace_relative = (_get_config_path().parent / path_obj).resolve()
    if workspace_relative.exists():
        return workspace_relative

    return candidate


def to_relative_path(path_like: Union[str, Path]) -> str:
    abs_path = Path(path_like).resolve()
    root = get_project_root()
    try:
        rel = abs_path.relative_to(root)
    except ValueError:
        rel = Path(os.path.relpath(abs_path, root))
    return rel.as_posix()


__all__ = [
    "AnalyzerConfigError",
    "CONFIG_ENV_VAR",
    "get_config_path",
    "get_project_root",
    "get_output_dir",
    "to_absolute_path",
    "to_relative_path",
    "resolve_output_path",
]
