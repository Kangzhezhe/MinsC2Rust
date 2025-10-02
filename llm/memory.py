"""Conversation memory management strategies for LLM agents.

This module provides a collection of pluggable memory strategies that help keep the
input context sent to the language model within practical bounds while preserving
important conversational facts.  The design follows the "pre_model_hook" concept
popularised in the LangGraph ecosystem: every strategy exposes a callable that can
trim or transform the list of messages right before they are forwarded to the LLM.

The strategies implemented here are inspired by the article
"AI Agent&MCP的工程化实践-系列3-模型上下文过长的解决方案" and include:

* :class:`NoOpStrategy`          – pass through, mainly for debugging
* :class:`SlidingWindowStrategy` – keep the most recent *N* messages
* :class:`TokenLimitStrategy`    – keep the newest messages within a token budget
* :class:`SummaryStrategy`       – summarise older messages while keeping the recent ones

All strategies work on a simple list of ``{"role": str, "content": str}``
message dictionaries (compatible with the native OpenAI / LangChain chat format).
The factory :func:`create_memory_strategy` can be used to build a strategy instance
from a human friendly configuration (string name or dictionary).
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union

Message = MutableMapping[str, Any]
Messages = Sequence[Message]

try:  # pragma: no cover - optional dependency
    import tiktoken
except ImportError:  # pragma: no cover - fallback path
    tiktoken = None


def _default_token_estimator(message: Mapping[str, Any]) -> int:
    """Rudimentary token estimator used when :mod:`tiktoken` is unavailable."""

    text = str(message.get("content", ""))
    if not text:
        return 1
    # Heuristic: average English token is ~4 characters.
    return max(1, math.ceil(len(text) / 4))


def _normalize_message(
    message: Any,
    *,
    default_role: str = "assistant",
) -> Message:
    """Convert an arbitrary message payload into the canonical mapping format."""

    if isinstance(message, MutableMapping):
        msg_dict = dict(message)
    elif isinstance(message, Mapping):
        msg_dict = dict(message)
    elif isinstance(message, str):
        msg_dict = {"role": default_role, "content": message}
    else:
        if hasattr(message, "role") and hasattr(message, "content"):
            msg_dict = {"role": getattr(message, "role"), "content": getattr(message, "content")}
        else:
            try:
                msg_dict = dict(message)  # type: ignore[arg-type]
            except Exception:
                msg_dict = {"role": default_role, "content": str(message)}

    role = msg_dict.get("role") or default_role
    content = msg_dict.get("content", "")

    msg_dict["role"] = str(role)
    msg_dict["content"] = "" if content is None else str(content)
    return msg_dict


def _normalize_messages(
    messages: Optional[Iterable[Any]],
    *,
    default_role: str = "assistant",
) -> List[Message]:
    if messages is None:
        return []
    return [_normalize_message(msg, default_role=default_role) for msg in messages]


class BaseMemoryStrategy:
    """Base class for all memory strategies."""

    def __init__(self, *, verbose: bool = False) -> None:
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, messages: Messages) -> List[Message]:
        """Return the messages that should be forwarded to the LLM.

        The default implementation simply clones the incoming sequence. Sub-classes
        override this to provide the actual trimming / summarisation behaviour.
        """

        return _normalize_messages(messages)

    def reset(self) -> None:
        """Reset any internal state kept by the strategy."""

    def create_pre_model_hook(self) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Return a hook compatible with LangGraph style "pre_model_hook".

        The hook expects a state dictionary with a ``"messages"`` key and returns
        a dictionary containing the trimmed list under ``"llm_input_messages"``.
        """

        def _hook(state: Dict[str, Any]) -> Dict[str, Any]:
            original = state.get("messages", [])
            trimmed = self.process(original)
            return {"llm_input_messages": trimmed}

        return _hook

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _debug(self, message: str) -> None:
        if self.verbose:
            print(message)


class NoOpStrategy(BaseMemoryStrategy):
    """Strategy that forwards all messages unchanged."""

    pass


class SlidingWindowStrategy(BaseMemoryStrategy):
    """Keep only the most recent *max_messages* non-system messages."""

    def __init__(self, max_messages: int = 10, *, verbose: bool = False) -> None:
        if max_messages <= 0:
            raise ValueError("max_messages 必须为正整数")
        super().__init__(verbose=verbose)
        self.max_messages = max_messages

    def process(self, messages: Messages) -> List[Message]:
        cloned = _normalize_messages(messages)
        system_messages = [m for m in cloned if m.get("role") == "system"]
        other_messages = [m for m in cloned if m.get("role") != "system"]
        trimmed_other = other_messages[-self.max_messages :]
        trimmed_messages = system_messages + trimmed_other
        self._debug(
            f"🧠 [滑动窗口] 消息修剪: {len(messages)} -> {len(trimmed_messages)}"
        )
        return trimmed_messages


class TokenLimitStrategy(BaseMemoryStrategy):
    """Keep messages so that the total token budget is not exceeded."""

    def __init__(
        self,
        max_tokens: int,
        *,
        model: Optional[str] = None,
        token_counter: Optional[Callable[[Mapping[str, Any]], int]] = None,
        safety_margin: int = 0,
        verbose: bool = False,
    ) -> None:
        if max_tokens <= 0:
            raise ValueError("max_tokens 必须为正整数")
        super().__init__(verbose=verbose)
        self.max_tokens = max_tokens
        self.safety_margin = max(0, safety_margin)
        self._token_counter = token_counter
        self._encoding = None
        if token_counter is None and tiktoken is not None:
            try:
                if model:
                    self._encoding = tiktoken.encoding_for_model(model)
                else:
                    self._encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:  # pragma: no cover - defensive fallback
                self._encoding = None

    def _count_tokens(self, message: Mapping[str, Any]) -> int:
        if self._token_counter:
            return max(1, int(self._token_counter(message)))
        if self._encoding is not None:  # pragma: no cover - requires tiktoken
            text = str(message.get("content", ""))
            return max(1, len(self._encoding.encode(text)))
        return _default_token_estimator(message)

    def process(self, messages: Messages) -> List[Message]:
        cloned = _normalize_messages(messages)
        system_messages = [m for m in cloned if m.get("role") == "system"]
        other_messages = [m for m in cloned if m.get("role") != "system"]

        budget = self.max_tokens - self.safety_margin
        used = sum(self._count_tokens(m) for m in system_messages)
        if used >= budget:
            self._debug("🧠 [Token限制] 系统消息已占满预算，返回系统消息")
            return system_messages

        kept: List[Message] = []
        # iterate from newest to oldest
        for message in reversed(other_messages):
            tokens = self._count_tokens(message)
            if kept and used + tokens > budget:
                break
            kept.append(message)
            used += tokens

        if not kept and other_messages:
            # 必须至少保留最新一条
            kept.append(other_messages[-1])

        trimmed = system_messages + list(reversed(kept))
        self._debug(
            f"🧠 [Token限制] 预算 {self.max_tokens}，保留 {len(trimmed)} 条消息"
        )
        return trimmed


@dataclass
class _Checkpoint:
    summary: str
    message_count: int


class SummaryStrategy(BaseMemoryStrategy):
    """Summarise older messages while keeping the latest ones verbatim."""

    def __init__(
        self,
        summarizer: Callable[[str], str],
        *,
        keep_recent: int = 4,
        summary_max_tokens: int = 3000,
        checkpoint_interval: int = 10,
        token_trigger_max_tokens: Optional[int] = None,
        token_counter: Optional[Callable[[Mapping[str, Any]], int]] = None,
        verbose: bool = False,
    ) -> None:
        if keep_recent < 0:
            raise ValueError("keep_recent 不能为负数")
        if checkpoint_interval <= 0:
            raise ValueError("checkpoint_interval 必须为正整数")
        if summary_max_tokens <= 0:
            raise ValueError("summary_max_tokens 必须为正整数")
        if token_trigger_max_tokens is not None and token_trigger_max_tokens <= 0:
            raise ValueError("token_trigger_max_tokens 必须为正整数")
        super().__init__(verbose=verbose)
        self.summarizer = summarizer
        self.keep_recent = keep_recent
        self.summary_max_tokens = summary_max_tokens
        self.checkpoint_interval = checkpoint_interval
        self.token_trigger_max_tokens = token_trigger_max_tokens
        self._token_counter = token_counter
        self._encoding = None
        if (
            self._token_counter is None
            and self.token_trigger_max_tokens is not None
            and tiktoken is not None
        ):
            try:
                self._encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:  # pragma: no cover - defensive fallback
                self._encoding = None
        self._checkpoints: Dict[int, _Checkpoint] = {}

    def reset(self) -> None:
        self._checkpoints.clear()

    def _count_tokens(self, message: Mapping[str, Any]) -> int:
        if self._token_counter is not None:
            try:
                return max(1, int(self._token_counter(message)))
            except Exception:
                return 1
        if self._encoding is not None:  # pragma: no cover - requires tiktoken
            text = str(message.get("content", ""))
            return max(1, len(self._encoding.encode(text)))
        return _default_token_estimator(message)

    def _format_messages(self, messages: Sequence[Message], start_index: int = 1) -> str:
        lines = []
        for offset, message in enumerate(messages, start=start_index):
            role = message.get("role", "unknown")
            content = str(message.get("content", "")).strip()
            lines.append(f"{offset}. {role}: {content}")
        return "\n".join(lines)

    def _call_summarizer(self, prompt: str) -> str:
        try:
            summary = self.summarizer(prompt)
        except Exception as exc:  # pragma: no cover - defensive fallback
            warnings.warn(f"摘要生成失败，返回提示文本: {exc}")
            return prompt
        return str(summary).strip()

    def _build_summary(
        self,
        to_summarise: Sequence[Message],
        start_index: int,
        end_index: int,
        previous_summary: Optional[_Checkpoint],
        system_messages: Optional[Sequence[Message]] = None,
    ) -> _Checkpoint:
        if previous_summary is not None and start_index < previous_summary.message_count:
            raise ValueError("start_index 不能小于上一个检查点的消息数")

        if previous_summary is not None:
            base_summary = previous_summary.summary
            new_messages = to_summarise[previous_summary.message_count : end_index]
            if not new_messages:
                return previous_summary
            new_text = self._format_messages(
                new_messages, start_index=previous_summary.message_count + 1
            )
            prompt = (
                f"用户提供的系统消息：{system_messages}\n"
                f"请生成包含所有对话历史总结的新累积摘要，尽量保留与系统消息相关的摘要（不超过{self.summary_max_tokens}个字符）。"
                f"之前的累积摘要（包含前{previous_summary.message_count}条消息）：{base_summary}\n"
                f"新增的对话内容（第{previous_summary.message_count + 1}到{end_index}条）：{new_text}\n"
            )
        else:
            conversation_text = self._format_messages(to_summarise[:end_index])
            prompt = (
                f"用户提供的系统消息：{system_messages}\n"
                f"请将以下对话历史总结成摘要，尽量保留与系统消息相关的摘要（不超过{self.summary_max_tokens}个字符）：\n"
                f"{conversation_text}"
            )

        summary_text = self._call_summarizer(prompt)
        self._debug(f"🧠 [摘要策略] 创建检查点 #{end_index}")
        return _Checkpoint(summary=summary_text, message_count=end_index)

    def process(self, messages: Messages) -> List[Message]:
        cloned = _normalize_messages(messages)
        system_messages = [m for m in cloned if m.get("role") == "system"]
        other_messages = [m for m in cloned if m.get("role") != "system"]
        if len(other_messages) <= self.keep_recent + 1:
            return cloned

        to_summarise = other_messages[:-self.keep_recent]
        recent_messages = other_messages[-self.keep_recent :]
        current_count = len(to_summarise)
        if current_count == 0:
            return cloned

        checkpoint_counts = sorted(k for k in self._checkpoints if k <= current_count)
        last_checkpoint = self._checkpoints[checkpoint_counts[-1]] if checkpoint_counts else None
        last_count = last_checkpoint.message_count if last_checkpoint else 0

        tokens_exceeded = False
        if self.token_trigger_max_tokens is not None:
            total_tokens = sum(self._count_tokens(m) for m in to_summarise)
            tokens_exceeded = total_tokens >= self.token_trigger_max_tokens
            if tokens_exceeded:
                self._debug(
                    "🧠 [摘要策略] 触发 token 阈值: {} / {}".format(
                        total_tokens, self.token_trigger_max_tokens
                    )
                )

        need_new_checkpoint = (
            current_count >= self.checkpoint_interval
            and (
                last_checkpoint is None
                or current_count - last_count >= self.checkpoint_interval
            )
        )

        if need_new_checkpoint or tokens_exceeded or last_checkpoint is None:
            start_index = (
                last_checkpoint.message_count + 1 if last_checkpoint is not None else 1
            )
            checkpoint = self._build_summary(
                to_summarise,
                start_index=start_index,
                end_index=current_count,
                previous_summary=last_checkpoint,
                system_messages=system_messages
            )
            self._checkpoints[current_count] = checkpoint
            summary_checkpoint = checkpoint
        else:
            summary_checkpoint = last_checkpoint
            self._debug(
                f"🧠 [摘要策略] 使用检查点 #{summary_checkpoint.message_count} 的累积摘要"
            )

        summarized_count = summary_checkpoint.message_count
        summary_message: Message = {
            "role": "system",
            "content": (
                f"【累积对话摘要（前{summarized_count}条消息）】\n"
                f"{summary_checkpoint.summary}"
            ),
        }

        unsummarised_messages = (
            to_summarise[summarized_count:] if summarized_count < len(to_summarise) else []
        )

        trimmed_messages = (
            system_messages
            + [summary_message]
            + list(unsummarised_messages)
            + recent_messages
        )

        self._debug(
            "🧠 [摘要策略] 最终消息构成: 系统({}) + 摘要(1) + 未摘要({}) + 最近({})".format(
                len(system_messages), len(unsummarised_messages), len(recent_messages)
            )
        )
        return trimmed_messages


StrategyConfig = Union[str, Mapping[str, Any], BaseMemoryStrategy, None]


def create_memory_strategy(
    config: StrategyConfig,
    *,
    summarizer: Optional[Callable[[str], str]] = None,
    token_counter: Optional[Callable[[Mapping[str, Any]], int]] = None,
    **kwargs: Any,
) -> Optional[BaseMemoryStrategy]:
    """Create a memory strategy from a configuration object.

    Parameters
    ----------
    config:
        Strategy specification.  It can be ``None`` (disable memory management), a
        string alias (e.g. ``"sliding_window"``), a mapping with a ``name`` field
        and optional parameters, or an already instantiated :class:`BaseMemoryStrategy`.
    summarizer:
        Callable used by :class:`SummaryStrategy`.  Required when the configuration
        requests that strategy and no instance is supplied explicitly.
    token_counter:
        Optional callable for :class:`TokenLimitStrategy` to override token counting.
    kwargs:
        Additional keyword overrides applied on top of the configuration mapping.
    """

    if config is None:
        return None
    if isinstance(config, BaseMemoryStrategy):
        return config
    if isinstance(config, str):
        name = config
        params: Dict[str, Any] = {}
    elif isinstance(config, Mapping):
        name = str(config.get("name"))
        params = {k: v for k, v in config.items() if k != "name"}
    else:
        raise TypeError("memory strategy 配置必须为字符串、映射或 BaseMemoryStrategy 实例")

    params.update(kwargs)
    key = name.lower()

    if key in {"noop", "none", "noopstrategy"}:
        return NoOpStrategy(**params)
    if key in {"sliding", "sliding_window", "slidingwindow", "slidingwindowstrategy"}:
        return SlidingWindowStrategy(**params)
    if key in {"token", "token_limit", "tokenlimit", "tokenlimitstrategy"}:
        if "token_counter" not in params and token_counter is not None:
            params.setdefault("token_counter", token_counter)
        return TokenLimitStrategy(**params)
    if key in {"summary", "summary_strategy", "summarystrategy"}:
        summarizer_fn = params.pop("summarizer", summarizer)
        if summarizer_fn is None:
            raise ValueError("SummaryStrategy 需要提供 summarizer 函数")
        if "token_counter" not in params and token_counter is not None:
            params.setdefault("token_counter", token_counter)
        return SummaryStrategy(summarizer=summarizer_fn, **params)

    raise ValueError(f"未知的 memory strategy: {name}")


__all__ = [
    "BaseMemoryStrategy",
    "NoOpStrategy",
    "SlidingWindowStrategy",
    "TokenLimitStrategy",
    "SummaryStrategy",
    "create_memory_strategy",
]
