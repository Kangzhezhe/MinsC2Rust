from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Union

import yaml

CONFIG_FILENAME = "analyzer_config.yaml"
CONFIG_PATH = Path(__file__).resolve().parents[1] / CONFIG_FILENAME
_ANALYZER_DIR = Path(__file__).resolve().parent


class AnalyzerConfigError(RuntimeError):
    """Raised when the analyzer configuration cannot be loaded or is invalid."""


@lru_cache(maxsize=1)
def _load_config_dict() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise AnalyzerConfigError(f"配置文件未找到: {CONFIG_PATH}")
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:  # type: ignore[attr-defined]
        raise AnalyzerConfigError(f"配置文件解析失败: {exc}") from exc

    if not isinstance(data, dict):
        raise AnalyzerConfigError("配置文件根结点必须是映射对象")
    return data


@lru_cache(maxsize=1)
def get_project_root() -> Path:
    data = _load_config_dict()
    root_value = data.get("project_root")
    if not root_value:
        raise AnalyzerConfigError("配置文件缺少 project_root")

    root_path = Path(root_value)
    if not root_path.is_absolute():
        root_path = (CONFIG_PATH.parent / root_path).resolve()
    return root_path


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

    workspace_relative = (CONFIG_PATH.parent / path_obj).resolve()
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
    "CONFIG_PATH",
    "get_project_root",
    "to_absolute_path",
    "to_relative_path",
]
