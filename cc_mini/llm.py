from __future__ import annotations

import json
import os
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import anthropic
import httpx


_OPENAI_IMPORT_ERROR: Exception | None = None

try:
    from openai import OpenAI
    import openai
except Exception as exc:  # pragma: no cover - exercised in tests via stubs
    OpenAI = None  # type: ignore[assignment]
    openai = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = exc


ProviderName = str

_ANTHROPIC_PROVIDER = "anthropic"
_OPENAI_PROVIDER = "openai"
_VALID_PROVIDERS = {_ANTHROPIC_PROVIDER, _OPENAI_PROVIDER}

_LOG_FILE_ENV = "CC_MINI_LLM_LOG_FILE"
_DEFAULT_LOG_FILE = "cc-mini-llm.log"
_RAW_LOG_FILE_ENV = "CC_MINI_LLM_RAW_LOG_FILE"
_DEFAULT_RAW_LOG_FILE = "cc-mini-llm-raw.txt"


@dataclass
class LLMUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


@dataclass
class LLMMessage:
    content: list[dict[str, Any]]
    usage: LLMUsage | None = None
    provider: str | None = None
    model: str | None = None
    fallback_used: bool = False
    raw_summary: dict[str, Any] | None = None


@dataclass(frozen=True)
class LLMThinkingConfig:
    enabled: bool = True


@dataclass(frozen=True)
class LLMFallbackConfig:
    enabled: bool = False
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    openai_extra_body: dict[str, Any] | None = None
    thinking: LLMThinkingConfig | None = None


class UpstreamEmptyOutputError(RuntimeError):
    pass


class ReasoningLengthEmptyError(UpstreamEmptyOutputError):
    pass


def validate_provider(provider: str | None) -> ProviderName:
    normalized = (provider or _ANTHROPIC_PROVIDER).strip().lower()
    if normalized not in _VALID_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    return normalized


def default_model_for_provider(provider: str) -> str:
    provider = validate_provider(provider)
    if provider == _OPENAI_PROVIDER:
        return "gpt-4.1-mini"
    return "claude-sonnet-4-20250514"


def default_companion_model(provider: str, model: str) -> str:
    provider = validate_provider(provider)
    if provider == _OPENAI_PROVIDER:
        return model
    return "claude-haiku-4-5-20251001"


def default_max_tokens_for_provider(provider: str) -> int:
    provider = validate_provider(provider)
    if provider == _OPENAI_PROVIDER:
        return 8192
    return 32000


def supports_reasoning_effort(provider: str, model: str) -> bool:
    provider = validate_provider(provider)
    if provider != _OPENAI_PROVIDER:
        return False
    lowered = model.lower()
    return lowered.startswith(("gpt-5", "o1", "o3", "o4","deepseek"))


class LLMClient:
    def __init__(
        self,
        provider: str = _ANTHROPIC_PROVIDER,
        api_key: str | None = None,
        base_url: str | None = None,
        openai_extra_body: dict[str, Any] | None = None,
        thinking: LLMThinkingConfig | None = None,
        fallback: LLMFallbackConfig | None = None,
    ):
        self.provider = validate_provider(provider)
        self._api_key = api_key
        self._base_url = base_url
        self._openai_extra_body = dict(openai_extra_body or {}) or None
        self._thinking = thinking or LLMThinkingConfig()
        self._fallback_config = fallback if fallback and fallback.enabled else None
        self._fallback_client = None
        self._status_events: list[str] = []
        self._llm_log_file = Path(os.getenv(_LOG_FILE_ENV, _DEFAULT_LOG_FILE)).expanduser()
        self._llm_raw_log_file = Path(os.getenv(_RAW_LOG_FILE_ENV, _DEFAULT_RAW_LOG_FILE)).expanduser()
        self._client = self._build_client(self.provider, api_key, base_url)

    @staticmethod
    def _build_client(provider: str, api_key: str | None, base_url: str | None) -> Any:
        provider = validate_provider(provider)
        if provider == _OPENAI_PROVIDER:
            if OpenAI is None:
                message = "OpenAI support requires the `openai` package to be installed."
                if _OPENAI_IMPORT_ERROR is not None:
                    message += f" Import failed: {_OPENAI_IMPORT_ERROR}"
                raise ValueError(message)
            return OpenAI(api_key=api_key, base_url=base_url)
        return anthropic.Anthropic(api_key=api_key, base_url=base_url)

    @property
    def has_fallback(self) -> bool:
        return self._fallback_config is not None

    def consume_status_events(self) -> list[str]:
        events = list(self._status_events)
        self._status_events.clear()
        return events

    def close(self) -> None:
        for attr in ("_client", "_fallback_client"):
            client = getattr(self, attr, None)
            close = getattr(client, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        self._fallback_client = None

    def create_message(
        self,
        *,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        effort: str | None = None,
        fallback_only: bool = False,
        fallback_reason: str = "",
    ) -> LLMMessage:
        if fallback_only:
            response = self._create_fallback_message(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                system=system,
                tools=tools,
                effort=effort,
                reason=fallback_reason or "forced fallback request",
            )
            self._status_events.append(
                "[CC-MINI-FALLBACK] fallback succeeded "
                + f"provider={response.provider} model={response.model}"
            )
            return response

        primary_extra_body = _with_thinking_extra_body(
            self._openai_extra_body,
            self._thinking,
            base_url=self._base_url,
        )
        request_payload = self._request_payload(
            provider=self.provider,
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools,
            effort=effort,
            openai_extra_body=primary_extra_body,
            thinking=self._thinking,
        )
        self._append_llm_log("request", request_payload)
        self._append_raw_transcript("INPUT", self._render_request_text(system, messages))

        try:
            response = self._create_message_once(
                provider=self.provider,
                client=self._client,
                base_url=self._base_url,
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                system=system,
                tools=tools,
                effort=effort,
                openai_extra_body=primary_extra_body,
                thinking=self._thinking,
            )
            response.provider = self.provider
            response.model = model
            self._validate_non_empty_response(response, provider=self.provider, model=model)
            self._append_response_log("response", self.provider, model, response)
            self._append_raw_transcript("OUTPUT", self._blocks_to_text(response.content))
            return response
        except Exception as primary_exc:
            if self.is_reasoning_length_empty_error(primary_exc):
                raise
            if self._fallback_config is None:
                raise
            reason = self.error_message(primary_exc)
            self._append_llm_log(
                "fallback_trigger",
                {
                    "primary_provider": self.provider,
                    "primary_model": model,
                    "reason": reason,
                },
            )
            self._status_events.append(
                "[CC-MINI-FALLBACK] primary failed; trying fallback "
                + self._fallback_label(model=model, reason=reason)
            )
            try:
                fallback_response = self._create_fallback_message(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    system=system,
                    tools=tools,
                    effort=effort,
                    reason=reason,
                )
            except Exception as fallback_exc:
                fallback_reason = self.error_message(fallback_exc)
                self._append_llm_log(
                    "fallback_error",
                    {
                        "primary_provider": self.provider,
                        "primary_model": model,
                        "primary_error": reason,
                        "fallback_error": fallback_reason,
                    },
                )
                self._status_events.append(
                    f"[CC-MINI-FALLBACK] fallback failed: {fallback_reason}"
                )
                raise primary_exc
            self._status_events.append(
                "[CC-MINI-FALLBACK] fallback succeeded "
                + f"provider={fallback_response.provider} model={fallback_response.model}"
            )
            return fallback_response

    def _request_payload(
        self,
        *,
        provider: str,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
        effort: str | None,
        fallback: bool = False,
        reason: str = "",
        base_url: str | None = None,
        openai_extra_body: dict[str, Any] | None = None,
        thinking: LLMThinkingConfig | None = None,
    ) -> dict[str, Any]:
        payload = {
            "provider": provider,
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": _messages_for_log(messages),
            "tools": tools or [],
            "effort": effort,
        }
        if openai_extra_body:
            payload["openai_extra_body"] = openai_extra_body
        if thinking is not None:
            payload["thinking"] = {"enabled": bool(thinking.enabled)}
        if fallback:
            payload["fallback"] = True
            payload["reason"] = reason
            payload["base_url"] = base_url
            payload["api_key_configured"] = bool((self._fallback_config and self._fallback_config.api_key) or self._api_key)
        return payload

    def _create_message_once(
        self,
        *,
        provider: str,
        client: Any,
        base_url: str | None,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
        effort: str | None,
        openai_extra_body: dict[str, Any] | None,
        thinking: LLMThinkingConfig | None,
    ) -> LLMMessage:
        provider = validate_provider(provider)
        if provider == _OPENAI_PROVIDER:
            return self._openai_create_message(
                client=client,
                base_url=base_url,
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                system=system,
                tools=tools,
                effort=effort,
                openai_extra_body=openai_extra_body,
                thinking=thinking,
            )
        return self._anthropic_create_message(
            client=client,
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            tools=tools,
        )

    def _create_fallback_message(
        self,
        *,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
        effort: str | None,
        reason: str,
    ) -> LLMMessage:
        if self._fallback_config is None:
            raise RuntimeError("fallback is not configured")
        fallback_provider = validate_provider(self._fallback_config.provider or self.provider)
        fallback_model = self._fallback_config.model or model
        fallback_client = self._get_fallback_client(fallback_provider)
        fallback_base_url = self._fallback_config.base_url or self._base_url
        fallback_thinking = self._fallback_config.thinking or LLMThinkingConfig()
        fallback_extra_body = (
            self._fallback_config.openai_extra_body
            if self._fallback_config.openai_extra_body is not None
            else self._openai_extra_body
        )
        fallback_extra_body = _with_thinking_extra_body(
            fallback_extra_body,
            fallback_thinking,
            base_url=fallback_base_url,
        )
        self._append_llm_log(
            "fallback_request",
            self._request_payload(
                provider=fallback_provider,
                model=fallback_model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                tools=tools,
                effort=effort,
                fallback=True,
                reason=reason,
                base_url=fallback_base_url,
                openai_extra_body=fallback_extra_body,
                thinking=fallback_thinking,
            ),
        )
        response = self._create_message_once(
            provider=fallback_provider,
            client=fallback_client,
            base_url=fallback_base_url,
            model=fallback_model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            tools=tools,
            effort=effort,
            openai_extra_body=fallback_extra_body,
            thinking=fallback_thinking,
        )
        response.provider = fallback_provider
        response.model = fallback_model
        response.fallback_used = True
        self._validate_non_empty_response(response, provider=fallback_provider, model=fallback_model, fallback=True)
        self._append_response_log("fallback_response", fallback_provider, fallback_model, response)
        self._append_raw_transcript("FALLBACK OUTPUT", self._blocks_to_text(response.content))
        return response

    def _get_fallback_client(self, fallback_provider: str) -> Any:
        if self._fallback_client is None:
            cfg = self._fallback_config
            if cfg is None:
                raise RuntimeError("fallback is not configured")
            self._fallback_client = self._build_client(
                fallback_provider,
                cfg.api_key or self._api_key,
                cfg.base_url or self._base_url,
            )
        return self._fallback_client

    def _fallback_label(self, *, model: str, reason: str) -> str:
        cfg = self._fallback_config
        if cfg is None:
            return ""
        return (
            f"provider={validate_provider(cfg.provider or self.provider)} "
            f"model={cfg.model or model} "
            f"base_url={cfg.base_url or self._base_url or ''} "
            f"reason={reason[:200]}"
        )

    def _append_response_log(self, direction: str, provider: str, model: str, response: LLMMessage) -> None:
        self._append_llm_log(
            direction,
            {
                "provider": provider,
                "model": model,
                "usage": _usage_to_dict(response.usage),
                "content": _content_for_log(response.content),
                "fallback": bool(response.fallback_used),
            },
        )

    def _validate_non_empty_response(
        self,
        response: LLMMessage,
        *,
        provider: str,
        model: str,
        fallback: bool = False,
    ) -> None:
        if not response.content:
            if _is_reasoning_length_empty_summary(response.raw_summary):
                self._append_llm_log(
                    "reasoning_length_empty",
                    {
                        "provider": provider,
                        "model": model,
                        "usage": _usage_to_dict(response.usage),
                        "raw_summary": response.raw_summary or {},
                        "fallback": fallback,
                    },
                )
                raise ReasoningLengthEmptyError("reasoning_length_empty")
            self._append_llm_log(
                "fallback_empty_response" if fallback else "empty_response",
                {
                    "provider": provider,
                    "model": model,
                    "usage": _usage_to_dict(response.usage),
                    "raw_summary": response.raw_summary or {},
                    "fallback": fallback,
                },
            )
            raise UpstreamEmptyOutputError("Upstream model returned empty output")

    def stream_messages(
        self,
        *,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        effort: str | None = None,
    ):
        request_payload = {
            "provider": self.provider,
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": _messages_for_log(messages),
            "tools": tools or [],
            "effort": effort,
            "stream": True,
        }
        primary_extra_body = _with_thinking_extra_body(
            self._openai_extra_body,
            self._thinking,
            base_url=self._base_url,
        )
        if primary_extra_body:
            request_payload["openai_extra_body"] = primary_extra_body
        request_payload["thinking"] = {"enabled": bool(self._thinking.enabled)}
        self._append_llm_log("request", request_payload)
        self._append_raw_transcript("INPUT", self._render_request_text(system, messages))

        if self.provider == _OPENAI_PROVIDER:
            return _OpenAIStream(
                client=self._client,
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                system=system,
                tools=tools or [],
                effort=effort,
                openai_extra_body=primary_extra_body,
                thinking=self._thinking,
                base_url=self._base_url,
                response_logger=self._append_llm_log,
                raw_logger=self._append_raw_transcript,
            )
        return _AnthropicStream(
            client=self._client,
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            system=system,
            tools=tools or [],
            response_logger=self._append_llm_log,
            raw_logger=self._append_raw_transcript,
            provider=self.provider,
        )

    def _append_llm_log(self, direction: str, payload: dict[str, Any]) -> None:
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "direction": direction,
            "payload": payload,
        }
        try:
            self._llm_log_file.parent.mkdir(parents=True, exist_ok=True)
            with self._llm_log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str))
                f.write("\n")
        except Exception:
            # 调试日志不可影响主流程
            return

    def _append_raw_transcript(self, role: str, text: str) -> None:
        if not text:
            return
        ts = datetime.now().isoformat(timespec="seconds")
        try:
            self._llm_raw_log_file.parent.mkdir(parents=True, exist_ok=True)
            with self._llm_raw_log_file.open("a", encoding="utf-8") as f:
                f.write(f"[{ts}] [{role}]\n{text}\n\n")
        except Exception:
            # 调试日志不可影响主流程
            return

    def _blocks_to_text(self, content: Any) -> str:
        return _blocks_to_text(content)

    def _render_request_text(self, system: str | None, messages: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        if system:
            lines.append("<<SYSTEM>>")
            lines.append(system)
        for message in messages:
            role = str(message.get("role", "unknown")).upper()
            lines.append(f"<<{role}>>")
            lines.append(_blocks_to_text(message.get("content", "")))
        return "\n".join(lines)

    def is_authentication_error(self, exc: Exception) -> bool:
        if self.provider == _OPENAI_PROVIDER:
            return openai is not None and isinstance(exc, openai.AuthenticationError)
        return isinstance(exc, anthropic.AuthenticationError)

    def is_retryable_error(self, exc: Exception) -> bool:
        if isinstance(exc, (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError)):
            return True
        if self.provider == _OPENAI_PROVIDER:
            return openai is not None and isinstance(
                exc,
                (
                    openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.InternalServerError,
                ),
            )
        return isinstance(
            exc,
            (
                anthropic.RateLimitError,
                anthropic.APIConnectionError,
                anthropic.InternalServerError,
            ),
        )

    def is_api_error(self, exc: Exception) -> bool:
        if self.provider == _OPENAI_PROVIDER:
            return openai is not None and isinstance(exc, openai.APIError)
        return isinstance(exc, anthropic.APIError)

    @staticmethod
    def error_message(exc: Exception) -> str:
        return str(getattr(exc, "message", None) or exc)

    def _anthropic_create_message(
        self,
        *,
        client: Any,
        base_url: str | None,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
    ) -> LLMMessage:
        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        response = client.messages.create(**kwargs)
        usage = _usage_from_anthropic(getattr(response, "usage", None))
        return LLMMessage(
            content=_normalize_anthropic_content(getattr(response, "content", [])),
            usage=usage,
            raw_summary=_summarize_anthropic_response(response),
        )

    def _openai_create_message(
        self,
        *,
        client: Any,
        base_url: str | None,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]] | None,
        effort: str | None,
        openai_extra_body: dict[str, Any] | None,
        thinking: LLMThinkingConfig | None,
    ) -> LLMMessage:
        params = _build_openai_request(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools or [],
            effort=effort,
            openai_extra_body=openai_extra_body,
            thinking=thinking,
            base_url=base_url,
            stream=False,
        )
        response = client.chat.completions.create(**params)
        choice = response.choices[0].message if response.choices else None
        usage = _usage_from_openai(getattr(response, "usage", None))
        return LLMMessage(
            content=_normalize_openai_message(
                choice,
                preserve_reasoning=bool(thinking and thinking.enabled),
            ),
            usage=usage,
            raw_summary=_summarize_openai_response(response),
        )

    @staticmethod
    def is_reasoning_length_empty_error(exc: Exception) -> bool:
        return isinstance(exc, ReasoningLengthEmptyError)


class _AnthropicStream:
    def __init__(
        self,
        *,
        client: Any,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]],
        response_logger: Any = None,
        raw_logger: Any = None,
        provider: str = _ANTHROPIC_PROVIDER,
    ):
        self._raw = client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tools,
            messages=messages,
        )
        self._ctx = None
        self._provider = provider
        self._model = model
        self._response_logger = response_logger
        self._raw_logger = raw_logger
        self.text_stream: Iterator[str] = iter(())

    def __enter__(self):
        self._ctx = self._raw.__enter__()
        self.text_stream = iter(self._ctx.text_stream)
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._raw.__exit__(exc_type, exc, tb)

    def close(self) -> None:
        if self._ctx is not None and hasattr(self._ctx, "close"):
            self._ctx.close()

    def get_final_message(self) -> LLMMessage:
        final = self._ctx.get_final_message()
        message = LLMMessage(
            content=_normalize_anthropic_content(getattr(final, "content", [])),
            usage=_usage_from_anthropic(getattr(final, "usage", None)),
        )
        if callable(self._response_logger):
            self._response_logger(
                "response",
                {
                    "provider": self._provider,
                    "model": self._model,
                    "usage": _usage_to_dict(message.usage),
                    "content": message.content,
                    "stream": True,
                },
            )
        if callable(self._raw_logger):
            self._raw_logger("OUTPUT", _blocks_to_text(message.content))
        return message


class _OpenAIStream:
    def __init__(
        self,
        *,
        client: Any,
        model: str,
        max_tokens: int,
        messages: list[dict[str, Any]],
        system: str | None,
        tools: list[dict[str, Any]],
        effort: str | None,
        openai_extra_body: dict[str, Any] | None,
        thinking: LLMThinkingConfig | None = None,
        base_url: str | None = None,
        response_logger: Any = None,
        raw_logger: Any = None,
    ):
        self._client = client
        self._model = model
        self._thinking = thinking or LLMThinkingConfig()
        self._response_logger = response_logger
        self._raw_logger = raw_logger
        self._params = _build_openai_request(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools,
            effort=effort,
            openai_extra_body=openai_extra_body,
            thinking=thinking,
            base_url=base_url,
            stream=True,
        )
        self._stream = None
        self._text_parts: list[str] = []
        self._reasoning_parts: list[str] = []
        self._reasoning_details: list[Any] = []
        self._finish_reasons: list[Any] = []
        self._tool_calls: dict[int, dict[str, Any]] = {}
        self._usage: LLMUsage | None = None
        self.text_stream: Iterator[str] = iter(())

    def __enter__(self):
        self._stream = self._client.chat.completions.create(**self._params)
        self.text_stream = self._iter_text()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def close(self) -> None:
        if self._stream is not None and hasattr(self._stream, "close"):
            self._stream.close()

    def _iter_text(self) -> Iterator[str]:
        for chunk in self._stream:
            usage = getattr(chunk, "usage", None)
            if usage is not None:
                self._usage = _usage_from_openai(usage)
            for choice in _value(chunk, "choices", []) or []:
                finish_reason = _value(choice, "finish_reason")
                if finish_reason is not None:
                    self._finish_reasons.append(finish_reason)
                delta = _value(choice, "delta", {}) or {}
                reasoning_content = _value(delta, "reasoning_content")
                if self._thinking.enabled and reasoning_content:
                    self._reasoning_parts.append(str(reasoning_content))
                reasoning_details = _value(delta, "reasoning_details")
                if self._thinking.enabled and reasoning_details:
                    if isinstance(reasoning_details, list):
                        self._reasoning_details.extend(reasoning_details)
                    else:
                        self._reasoning_details.append(reasoning_details)
                content = _value(delta, "content")
                if content:
                    self._text_parts.append(content)
                    yield content
                for tool_call in _value(delta, "tool_calls", []) or []:
                    index = int(_value(tool_call, "index", 0) or 0)
                    entry = self._tool_calls.setdefault(index, {
                        "id": "",
                        "name": "",
                        "arguments": "",
                    })
                    tool_id = _value(tool_call, "id")
                    if tool_id:
                        entry["id"] = tool_id
                    function = _value(tool_call, "function", {}) or {}
                    name = _value(function, "name")
                    if name:
                        entry["name"] = name
                    arguments = _value(function, "arguments")
                    if arguments:
                        entry["arguments"] += arguments

    def get_final_message(self) -> LLMMessage:
        content: list[dict[str, Any]] = []
        has_tool_calls = bool(self._tool_calls)
        raw_summary = self._raw_summary()
        if not self._text_parts and not has_tool_calls and _is_reasoning_length_empty_summary(raw_summary):
            if callable(self._response_logger):
                self._response_logger(
                    "reasoning_length_empty",
                    {
                        "provider": _OPENAI_PROVIDER,
                        "model": self._model,
                        "usage": _usage_to_dict(self._usage),
                        "raw_summary": raw_summary,
                        "stream": True,
                    },
                )
            raise ReasoningLengthEmptyError("reasoning_length_empty")
        if self._thinking.enabled and has_tool_calls:
            reasoning_text = "".join(self._reasoning_parts)
            if reasoning_text:
                content.append({"type": "reasoning", "text": reasoning_text})
            if self._reasoning_details:
                content.append({"type": "reasoning_details", "details": self._reasoning_details})
        text = "".join(self._text_parts)
        if text:
            content.append({"type": "text", "text": text})
        for index in sorted(self._tool_calls):
            tool_call = self._tool_calls[index]
            raw_args = tool_call.get("arguments", "").strip()
            parsed_args: Any = {}
            if raw_args:
                try:
                    parsed_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    parsed_args = {}
            content.append({
                "type": "tool_use",
                "id": tool_call.get("id", ""),
                "name": tool_call.get("name", ""),
                "input": parsed_args if isinstance(parsed_args, dict) else {},
            })
        message = LLMMessage(content=content, usage=self._usage, raw_summary=raw_summary)
        if callable(self._response_logger):
            self._response_logger(
                "response",
                {
                    "provider": _OPENAI_PROVIDER,
                    "model": self._model,
                    "usage": _usage_to_dict(message.usage),
                    "content": _content_for_log(message.content),
                    "stream": True,
                },
            )
        if callable(self._raw_logger):
            self._raw_logger("OUTPUT", _blocks_to_text(message.content))
        return message

    def _raw_summary(self) -> dict[str, Any]:
        text = "".join(self._text_parts)
        return {
            "provider": _OPENAI_PROVIDER,
            "stream": True,
            "usage": _usage_to_dict(self._usage),
            "choices": [
                {
                    "finish_reason": self._finish_reasons[-1] if self._finish_reasons else None,
                    "content_is_none": not bool(text),
                    "content_len": len(text),
                    "tool_calls_count": len(self._tool_calls),
                    "reasoning_content_present": bool(self._reasoning_parts),
                    "reasoning_content_len": sum(len(part) for part in self._reasoning_parts),
                    "reasoning_details_present": bool(self._reasoning_details),
                }
            ],
        }


def _normalize_anthropic_content(content: Any) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for block in content or []:
        normalized = _normalize_anthropic_block(block)
        if normalized is not None:
            blocks.append(normalized)
    return blocks


def _normalize_anthropic_block(block: Any) -> dict[str, Any] | None:
    block_type = _value(block, "type")
    if block_type == "text":
        return {"type": "text", "text": _value(block, "text", "")}
    if block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": _value(block, "id", ""),
            "name": _value(block, "name", ""),
            "input": _value(block, "input", {}) or {},
        }
    if block_type == "tool_result":
        normalized = {
            "type": "tool_result",
            "tool_use_id": _value(block, "tool_use_id", ""),
            "content": _value(block, "content", ""),
        }
        is_error = _value(block, "is_error")
        if is_error is not None:
            normalized["is_error"] = bool(is_error)
        return normalized
    if block_type == "image":
        return {
            "type": "image",
            "source": _value(block, "source", {}),
        }
    if isinstance(block, dict):
        return dict(block)
    if hasattr(block, "model_dump"):
        return block.model_dump()
    return None


def _normalize_openai_message(message: Any, preserve_reasoning: bool = False) -> list[dict[str, Any]]:
    if message is None:
        return []
    content: list[dict[str, Any]] = []
    raw_tool_calls = _value(message, "tool_calls", []) or []
    if preserve_reasoning and raw_tool_calls:
        reasoning_content = _value(message, "reasoning_content")
        if isinstance(reasoning_content, str) and reasoning_content:
            content.append({"type": "reasoning", "text": reasoning_content})
        reasoning_details = _value(message, "reasoning_details")
        if reasoning_details:
            content.append({"type": "reasoning_details", "details": reasoning_details})
    text = _extract_openai_text(_value(message, "content"))
    if text:
        content.append({"type": "text", "text": text})
    for tool_call in raw_tool_calls:
        arguments = _value(_value(tool_call, "function", {}) or {}, "arguments", "") or ""
        parsed_args: Any = {}
        if arguments:
            try:
                parsed_args = json.loads(arguments)
            except json.JSONDecodeError:
                parsed_args = {}
        content.append({
            "type": "tool_use",
            "id": _value(tool_call, "id", ""),
            "name": _value(_value(tool_call, "function", {}) or {}, "name", ""),
            "input": parsed_args if isinstance(parsed_args, dict) else {},
        })
    return content


def _with_thinking_extra_body(
    openai_extra_body: dict[str, Any] | None,
    thinking: LLMThinkingConfig | None,
    *,
    base_url: str | None,
) -> dict[str, Any] | None:
    if thinking is None:
        return dict(openai_extra_body or {}) or None

    extra_body = dict(openai_extra_body or {})
    extra_body.pop("thinking", None)
    extra_body.pop("enable_thinking", None)

    if _is_dashscope_base_url(base_url):
        extra_body["enable_thinking"] = bool(thinking.enabled)
    else:
        extra_body["thinking"] = {
            "type": "enabled" if thinking.enabled else "disabled",
        }
    return extra_body


def _is_dashscope_base_url(base_url: str | None) -> bool:
    return "dashscope.aliyuncs.com" in (base_url or "").lower()


def _messages_for_log(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    logged: list[dict[str, Any]] = []
    for message in messages:
        item = dict(message)
        item["content"] = _content_for_log(message.get("content", ""))
        logged.append(item)
    return logged


def _content_for_log(content: Any) -> Any:
    if not isinstance(content, list):
        return content
    logged: list[Any] = []
    for block in content:
        if not isinstance(block, dict):
            logged.append(block)
            continue
        block_type = block.get("type")
        if block_type == "reasoning":
            text = str(block.get("text", ""))
            logged.append({
                "type": "reasoning",
                "text_omitted": True,
                "text_len": len(text),
            })
            continue
        if block_type == "reasoning_details":
            details = block.get("details", [])
            logged.append({
                "type": "reasoning_details",
                "details_omitted": True,
                "details_count": len(details) if isinstance(details, list) else 1,
            })
            continue
        logged.append(block)
    return logged


def _is_reasoning_length_empty_summary(raw_summary: dict[str, Any] | None) -> bool:
    if not raw_summary:
        return False
    choices = raw_summary.get("choices")
    if not isinstance(choices, list) or not choices:
        return False
    choice = choices[0] if isinstance(choices[0], dict) else {}
    if choice.get("finish_reason") != "length":
        return False
    if not choice.get("reasoning_content_present"):
        return False
    if int(choice.get("tool_calls_count") or 0) != 0:
        return False
    content_len = choice.get("content_len")
    content_is_none = bool(choice.get("content_is_none"))
    return content_is_none or content_len == 0


def _summarize_openai_response(response: Any) -> dict[str, Any]:
    choices = _value(response, "choices", []) or []
    summary: dict[str, Any] = {
        "provider": _OPENAI_PROVIDER,
        "choice_count": len(choices),
        "usage": _usage_to_dict(_usage_from_openai(_value(response, "usage"))),
    }
    choice_summaries: list[dict[str, Any]] = []
    for index, choice in enumerate(choices[:3]):
        message = _value(choice, "message")
        content = _value(message, "content")
        tool_calls = _value(message, "tool_calls", []) or []
        reasoning_content = _value(message, "reasoning_content")
        reasoning = _value(message, "reasoning")
        refusal = _value(message, "refusal")
        annotations = _value(message, "annotations", []) or []
        choice_summaries.append(
            {
                "index": index,
                "finish_reason": _value(choice, "finish_reason"),
                "message_present": message is not None,
                "content_type": type(content).__name__ if content is not None else None,
                "content_is_none": content is None,
                "content_len": len(content) if isinstance(content, str) else None,
                "tool_calls_count": len(tool_calls),
                "tool_call_names": [
                    _value(_value(tool_call, "function", {}) or {}, "name")
                    for tool_call in tool_calls[:8]
                ],
                "reasoning_content_present": reasoning_content is not None,
                "reasoning_content_len": len(reasoning_content) if isinstance(reasoning_content, str) else None,
                "reasoning_present": reasoning is not None,
                "refusal_present": refusal is not None,
                "annotations_count": len(annotations),
            }
        )
    summary["choices"] = choice_summaries
    return summary


def _summarize_anthropic_response(response: Any) -> dict[str, Any]:
    content = _value(response, "content", []) or []
    return {
        "provider": _ANTHROPIC_PROVIDER,
        "stop_reason": _value(response, "stop_reason"),
        "stop_sequence": _value(response, "stop_sequence"),
        "content_count": len(content),
        "content_types": [_value(block, "type") for block in content[:12]],
        "usage": _usage_to_dict(_usage_from_anthropic(_value(response, "usage"))),
    }


def _extract_openai_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for item in content:
        item_type = _value(item, "type")
        if item_type == "text":
            text = _value(item, "text")
            if isinstance(text, str):
                parts.append(text)
            elif isinstance(text, dict):
                parts.append(str(text.get("value", "")))
    return "".join(parts)


def _blocks_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    if not isinstance(content, list):
        try:
            return json.dumps(content, ensure_ascii=False)
        except Exception:
            return str(content)

    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            parts.append(str(block))
            continue

        block_type = block.get("type")
        if block_type == "text":
            parts.append(str(block.get("text", "")))
        elif block_type == "tool_use":
            parts.append(
                f"[tool_use] {block.get('name', '')} {json.dumps(block.get('input', {}), ensure_ascii=False)}"
            )
        elif block_type == "tool_result":
            parts.append(f"[tool_result] {_tool_result_to_text(block.get('content', ''))}")
        elif block_type == "reasoning":
            parts.append(f"[reasoning]\n{str(block.get('text', ''))}")
        elif block_type == "reasoning_details":
            parts.append(
                "[reasoning_details]\n"
                + json.dumps(block.get("details", []), ensure_ascii=False, default=str)
            )
        else:
            parts.append(json.dumps(block, ensure_ascii=False))

    return "\n".join(p for p in parts if p)


def _usage_from_anthropic(usage: Any) -> LLMUsage | None:
    if usage is None:
        return None
    return LLMUsage(
        input_tokens=int(_value(usage, "input_tokens", 0) or 0),
        output_tokens=int(_value(usage, "output_tokens", 0) or 0),
        cache_read_input_tokens=int(_value(usage, "cache_read_input_tokens", 0) or 0),
        cache_creation_input_tokens=int(_value(usage, "cache_creation_input_tokens", 0) or 0),
    )


def _usage_from_openai(usage: Any) -> LLMUsage | None:
    if usage is None:
        return None
    return LLMUsage(
        input_tokens=int(_value(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(_value(usage, "completion_tokens", 0) or 0),
    )


def _usage_to_dict(usage: LLMUsage | None) -> dict[str, int] | None:
    if usage is None:
        return None
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_read_input_tokens": usage.cache_read_input_tokens,
        "cache_creation_input_tokens": usage.cache_creation_input_tokens,
    }


def _build_openai_request(
    *,
    model: str,
    max_tokens: int,
    system: str | None,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    effort: str | None,
    openai_extra_body: dict[str, Any] | None,
    thinking: LLMThinkingConfig | None = None,
    base_url: str | None = None,
    stream: bool,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "model": model,
        "messages": _to_openai_messages(system, messages),
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if tools:
        params["tools"] = [_tool_schema_to_openai(tool) for tool in tools]
    if effort and supports_reasoning_effort(_OPENAI_PROVIDER, model):
        params["reasoning_effort"] = effort
    extra_body = _with_thinking_extra_body(
        openai_extra_body,
        thinking,
        base_url=base_url,
    )
    if extra_body:
        params["extra_body"] = extra_body
    return params


def _to_openai_messages(system: str | None, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if system:
        out.append({"role": "system", "content": system})

    for message in messages:
        role = message.get("role")
        content = message.get("content", "")

        if role == "user" and isinstance(content, list):
            tool_results = [
                block for block in content
                if isinstance(block, dict) and block.get("type") == "tool_result"
            ]
            if tool_results and len(tool_results) == len(content):
                for block in tool_results:
                    out.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": _tool_result_to_text(block.get("content", "")),
                    })
                continue

            out.append({
                "role": "user",
                "content": _user_content_blocks_to_openai(content),
            })
            continue

        if role == "assistant" and isinstance(content, list):
            text_parts: list[str] = []
            reasoning_parts: list[str] = []
            reasoning_details: list[Any] | None = None
            tool_calls: list[dict[str, Any]] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "reasoning":
                    reasoning_parts.append(block.get("text", ""))
                elif block_type == "reasoning_details":
                    raw_details = block.get("details")
                    if reasoning_details is None:
                        reasoning_details = []
                    if isinstance(raw_details, list):
                        reasoning_details.extend(raw_details)
                    elif raw_details is not None:
                        reasoning_details.append(raw_details)
                elif block_type == "tool_use":
                    tool_calls.append({
                        "id": block.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(block.get("input", {}), ensure_ascii=False),
                        },
                    })
            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": "".join(text_parts) or None,
            }
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
                reasoning_text = "".join(reasoning_parts)
                if reasoning_text:
                    assistant_message["reasoning_content"] = reasoning_text
                if reasoning_details:
                    assistant_message["reasoning_details"] = reasoning_details
            out.append(assistant_message)
            continue

        out.append({
            "role": role,
            "content": content,
        })

    return out


def _user_content_blocks_to_openai(content: list[Any]) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            parts.append({"type": "text", "text": block.get("text", "")})
        elif block_type == "image":
            source = block.get("source", {})
            media_type = source.get("media_type", "image/png")
            data = source.get("data", "")
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{data}"},
            })
    if not parts:
        return [{"type": "text", "text": ""}]
    return parts


def _tool_schema_to_openai(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "parameters": tool.get("input_schema", {}),
        },
    }


def _tool_result_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    return json.dumps(content, ensure_ascii=False)


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)
