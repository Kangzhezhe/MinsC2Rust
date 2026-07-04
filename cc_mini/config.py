from __future__ import annotations

import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from .llm import (
    LLMFallbackConfig,
    LLMThinkingConfig,
    default_max_tokens_for_provider,
    default_model_for_provider,
    validate_provider,
)

load_dotenv()

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = default_model_for_provider(DEFAULT_PROVIDER)
_ANTHROPIC_FALLBACK_MAX_TOKENS = 32000
_OPENAI_FALLBACK_MAX_TOKENS = default_max_tokens_for_provider("openai")
_MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    "best": "claude-opus-4-6",
    "claude-opus-4.6": "claude-opus-4-6",
    "claude-opus-4.5": "claude-opus-4-5",
    "claude-opus-4.1": "claude-opus-4-1",
    "claude-opus-4": "claude-opus-4",
    "claude-sonnet-4.6": "claude-sonnet-4-6",
    "claude-sonnet-4.5": "claude-sonnet-4-5",
    "claude-sonnet-4": "claude-sonnet-4",
    "claude-3.7-sonnet": "claude-3-7-sonnet",
    "claude-3.5-sonnet": "claude-3-5-sonnet",
    "claude-3.5-haiku": "claude-3-5-haiku",
    "claude-3-haiku": "claude-3-haiku",
}
# First prefix match wins. Values from official getModelMaxOutputTokens().
_MODEL_MAX_TOKENS = (
    ("claude-opus-4-6", 64000),
    ("claude-sonnet-4-6", 32000),
    ("claude-opus-4-5", 32000),
    ("claude-sonnet-4-5", 32000),
    ("claude-sonnet-4", 32000),
    ("claude-haiku-4", 32000),
    ("claude-opus-4-1", 32000),
    ("claude-opus-4", 32000),
    ("claude-3-7-sonnet", 32000),
    ("claude-3-5-sonnet", 8192),
    ("claude-3-5-haiku", 8192),
    ("claude-3-haiku", 4096),
)
_ENV_MODEL = "CC_MINI_MODEL"
_ENV_MAX_TOKENS = "CC_MINI_MAX_TOKENS"
_ENV_MEMORY_DIR = "CC_MINI_MEMORY_DIR"
_ENV_PROVIDER = "CC_MINI_PROVIDER"
_ENV_EFFORT = "CC_MINI_EFFORT"
_ENV_STREAM = "CC_MINI_STREAM"
_DEFAULT_CONFIG_PATHS = (
    Path.home() / ".config" / "cc-mini" / "config.toml",
    Path.cwd() / ".cc-mini.toml",
)


@dataclass(frozen=True)
class AppConfig:
    provider: str
    api_key: str | None
    base_url: str | None
    model: str
    max_tokens: int
    effort: str | None = None
    stream: bool = False
    use_finish_tool: bool = False
    memory_dir: Path = Path.home() / ".mini-claude" / "memory"
    dream_interval_hours: float = 24.0
    dream_min_sessions: int = 5
    auto_dream: bool = True
    config_paths: tuple[Path, ...] = ()
    openai_extra_body: dict[str, Any] | None = None
    thinking: LLMThinkingConfig = LLMThinkingConfig()
    fallback: LLMFallbackConfig | None = None


def resolve_model(model: str | None, provider: str = DEFAULT_PROVIDER) -> str:
    provider = validate_provider(provider)
    if not model:
        return default_model_for_provider(provider)
    normalized = model.strip()
    if provider != "anthropic":
        return normalized
    return _MODEL_ALIASES.get(normalized, normalized)


def default_max_tokens_for_model(
    model: str | None,
    provider: str = DEFAULT_PROVIDER,
) -> int:
    provider = validate_provider(provider)
    resolved = resolve_model(model, provider=provider)
    if provider == "openai":
        openai_limits = (
            ("gpt-5", 8192),
            ("gpt-4.1", 16384),
            ("gpt-4o", 16384),
            ("o1", 32768),
            ("o3", 32768),
            ("o4", 32768),
        )
        for prefix, limit in openai_limits:
            if resolved.startswith(prefix):
                return limit
        return _OPENAI_FALLBACK_MAX_TOKENS

    for prefix, limit in _MODEL_MAX_TOKENS:
        if resolved.startswith(prefix):
            return limit
    return _ANTHROPIC_FALLBACK_MAX_TOKENS


def load_app_config(args: Namespace) -> AppConfig:
    file_values, config_paths = _load_file_values(args.config)
    env_values = _load_env_values()

    raw_provider = (
        getattr(args, "provider", None)
        or file_values["top"].get("provider")
        or env_values.get("provider")
    )
    provider = validate_provider(
        raw_provider or _infer_provider(file_values["providers"])
    )

    selected_provider_values = file_values["providers"].get(provider, {})
    selected_env_values = _provider_env_values(env_values, provider)

    def _file_value(key: str) -> Any:
        if key in file_values["top"]:
            return file_values["top"][key]
        return selected_provider_values.get(key)

    raw_model = args.model or _file_value("model") or env_values.get("model")
    model = resolve_model(raw_model, provider=provider)

    raw_max_tokens = (
        args.max_tokens
        if args.max_tokens is not None
        else (
            _file_value("max_tokens")
            if _file_value("max_tokens") is not None
            else env_values.get("max_tokens")
        )
    )
    max_tokens = _parse_max_tokens(
        raw_max_tokens,
        default=default_max_tokens_for_model(model, provider=provider),
    )

    raw_effort = getattr(args, "effort", None)
    if raw_effort is None:
        raw_effort = _file_value("effort")
        if raw_effort is None:
            raw_effort = env_values.get("effort")
    effort = _parse_effort(raw_effort)

    raw_stream = getattr(args, "stream", None)
    if raw_stream is None:
        raw_stream = _file_value("stream")
        if raw_stream is None:
            raw_stream = env_values.get("stream")
    stream = _parse_bool(raw_stream, default=False)

    raw_memory_dir = (
        getattr(args, "memory_dir", None)
        or _file_value("memory_dir")
        or env_values.get("memory_dir")
    )
    memory_dir = Path(raw_memory_dir).expanduser() if raw_memory_dir else Path.home() / ".mini-claude" / "memory"

    raw_dream_interval = getattr(args, "dream_interval", None)
    if raw_dream_interval is None:
        raw_dream_interval = _file_value("dream_interval_hours")
        if raw_dream_interval is None:
            raw_dream_interval = env_values.get("dream_interval_hours")
    dream_interval = float(raw_dream_interval) if raw_dream_interval is not None else 24.0

    raw_dream_min = getattr(args, "dream_min_sessions", None)
    if raw_dream_min is None:
        raw_dream_min = _file_value("dream_min_sessions")
        if raw_dream_min is None:
            raw_dream_min = env_values.get("dream_min_sessions")
    dream_min_sessions = int(raw_dream_min) if raw_dream_min is not None else 5
    auto_dream = True
    raw_auto_dream = _file_value("auto_dream")
    if raw_auto_dream is None:
        raw_auto_dream = env_values.get("auto_dream")
    if raw_auto_dream is not None:
        auto_dream = str(raw_auto_dream).lower() not in ("false", "0", "no")
    if getattr(args, "no_auto_dream", False):
        auto_dream = False

    raw_use_finish = getattr(args, "use_finish_tool", None)
    if raw_use_finish is None:
        raw_use_finish = _file_value("use_finish_tool")
        if raw_use_finish is None:
            raw_use_finish = env_values.get("use_finish_tool")
    use_finish_tool = str(raw_use_finish).lower() in ("true", "1", "yes") if raw_use_finish is not None else False
    openai_extra_body = _parse_extra_body(file_values.get("openai_extra_body"), "openai_extra_body")
    thinking = _parse_thinking_config(file_values.get("thinking"), "thinking")
    fallback = _build_fallback_config(file_values.get("fallback", {}), provider=provider)

    return AppConfig(
        provider=provider,
        api_key=args.api_key or _file_value("api_key") or selected_env_values.get("api_key"),
        base_url=args.base_url or _file_value("base_url") or selected_env_values.get("base_url"),
        model=model,
        max_tokens=max_tokens,
        effort=effort,
        stream=stream,
        use_finish_tool=use_finish_tool,
        memory_dir=memory_dir,
        dream_interval_hours=dream_interval,
        dream_min_sessions=dream_min_sessions,
        auto_dream=auto_dream,
        config_paths=config_paths,
        openai_extra_body=openai_extra_body,
        thinking=thinking,
        fallback=fallback,
    )


def _load_file_values(explicit_path: str | None) -> tuple[dict[str, Any], tuple[Path, ...]]:
    values: dict[str, Any] = {
        "top": {},
        "providers": {"anthropic": {}, "openai": {}},
        "openai_extra_body": {},
        "thinking": {},
        "fallback": {},
    }
    loaded_paths: list[Path] = []

    if explicit_path:
        path = Path(explicit_path).expanduser()
        if not path.exists():
            raise ValueError(f"Config file not found: {path}")
        _merge_file_values(values, _read_config_file(path))
        loaded_paths.append(path)
        return values, tuple(loaded_paths)

    for path in _DEFAULT_CONFIG_PATHS:
        if not path.exists():
            continue
        _merge_file_values(values, _read_config_file(path))
        loaded_paths.append(path)

    return values, tuple(loaded_paths)


def _read_config_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in config file {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read config file {path}: {exc}") from exc

    values: dict[str, Any] = {
        "top": {},
        "providers": {"anthropic": {}, "openai": {}},
        "openai_extra_body": {},
        "thinking": {},
        "fallback": {},
    }

    for provider in ("anthropic", "openai"):
        section = data.get(provider, {})
        if isinstance(section, dict):
            values["providers"][provider].update(section)
    fallback_section = data.get("fallback", {})
    if isinstance(fallback_section, dict):
        values["fallback"].update(fallback_section)
    openai_extra_body = data.get("openai_extra_body", {})
    if isinstance(openai_extra_body, dict):
        values["openai_extra_body"].update(openai_extra_body)
    thinking = data.get("thinking", {})
    if isinstance(thinking, dict):
        values["thinking"].update(thinking)

    for key in (
        "provider",
        "api_key",
        "base_url",
        "model",
        "max_tokens",
        "effort",
        "stream",
        "memory_dir",
        "dream_interval_hours",
        "dream_min_sessions",
        "auto_dream",
    ):
        if key in data:
            values["top"][key] = data[key]

    return values


def _load_env_values() -> dict[str, Any]:
    values: dict[str, Any] = {}
    if os.getenv(_ENV_PROVIDER):
        values["provider"] = os.environ[_ENV_PROVIDER]
    if os.getenv("OPENAI_API_KEY"):
        values["openai_api_key"] = os.environ["OPENAI_API_KEY"]
    if os.getenv("OPENAI_BASE_URL"):
        values["openai_base_url"] = os.environ["OPENAI_BASE_URL"]
    if os.getenv("ANTHROPIC_API_KEY"):
        values["anthropic_api_key"] = os.environ["ANTHROPIC_API_KEY"]
    if os.getenv("ANTHROPIC_BASE_URL"):
        values["anthropic_base_url"] = os.environ["ANTHROPIC_BASE_URL"]
    if os.getenv(_ENV_MODEL):
        values["model"] = os.environ[_ENV_MODEL]
    if os.getenv(_ENV_MAX_TOKENS):
        values["max_tokens"] = os.environ[_ENV_MAX_TOKENS]
    if os.getenv(_ENV_MEMORY_DIR):
        values["memory_dir"] = os.environ[_ENV_MEMORY_DIR]
    if os.getenv(_ENV_EFFORT):
        values["effort"] = os.environ[_ENV_EFFORT]
    if os.getenv(_ENV_STREAM):
        values["stream"] = os.environ[_ENV_STREAM]
    return values


def _parse_max_tokens(raw_value: Any, default: int) -> int:
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid max_tokens value: {raw_value!r}") from exc

    if value <= 0:
        raise ValueError("max_tokens must be a positive integer")
    return value


def _parse_effort(raw_value: Any) -> str | None:
    if raw_value is None:
        return None
    normalized = str(raw_value).strip().lower()
    if normalized not in ("low", "medium", "high","none"):
        raise ValueError("effort must be one of: low, medium, high")
    return normalized


def _parse_bool(raw_value: Any, *, default: bool) -> bool:
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    normalized = str(raw_value).strip().lower()
    if normalized in ("true", "1", "yes", "on"):
        return True
    if normalized in ("false", "0", "no", "off"):
        return False
    raise ValueError(f"Invalid boolean value: {raw_value!r}")


def _parse_extra_body(raw_value: Any, section_name: str) -> dict[str, Any] | None:
    if not raw_value:
        return None
    if not isinstance(raw_value, dict):
        raise ValueError(f"{section_name} must be a TOML table")
    return dict(raw_value)


def _parse_thinking_config(
    raw_value: Any,
    section_name: str,
    *,
    default_enabled: bool = True,
) -> LLMThinkingConfig:
    if raw_value is None:
        return LLMThinkingConfig(enabled=default_enabled)
    if not isinstance(raw_value, dict):
        raise ValueError(f"{section_name} must be a TOML table")
    return LLMThinkingConfig(
        enabled=_parse_bool(raw_value.get("enabled"), default=default_enabled),
    )


def _infer_provider(provider_values: dict[str, dict[str, Any]]) -> str:
    openai_values = provider_values.get("openai", {})
    anthropic_values = provider_values.get("anthropic", {})
    if openai_values and not anthropic_values:
        return "openai"
    return DEFAULT_PROVIDER


def _merge_file_values(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    target["top"].update(incoming.get("top", {}))
    for provider in ("anthropic", "openai"):
        target["providers"][provider].update(incoming.get("providers", {}).get(provider, {}))
    target.setdefault("openai_extra_body", {}).update(incoming.get("openai_extra_body", {}))
    target.setdefault("thinking", {}).update(incoming.get("thinking", {}))
    target.setdefault("fallback", {}).update(incoming.get("fallback", {}))


def _build_fallback_config(raw: dict[str, Any], *, provider: str) -> LLMFallbackConfig | None:
    enabled = _parse_bool(raw.get("enabled"), default=False)
    if not enabled:
        return None
    fallback_provider = validate_provider(raw.get("provider") or provider)
    return LLMFallbackConfig(
        enabled=True,
        provider=fallback_provider,
        api_key=raw.get("api_key"),
        base_url=raw.get("base_url"),
        model=resolve_model(raw.get("model"), provider=fallback_provider) if raw.get("model") else None,
        openai_extra_body=_parse_extra_body(
            raw.get("openai_extra_body"),
            "fallback.openai_extra_body",
        ),
        thinking=_parse_thinking_config(
            raw.get("thinking"),
            "fallback.thinking",
        ),
    )


def _provider_env_values(env_values: dict[str, Any], provider: str) -> dict[str, Any]:
    provider = validate_provider(provider)
    if provider == "openai":
        return {
            "api_key": env_values.get("openai_api_key"),
            "base_url": env_values.get("openai_base_url"),
        }
    return {
        "api_key": env_values.get("anthropic_api_key"),
        "base_url": env_values.get("anthropic_base_url"),
    }
