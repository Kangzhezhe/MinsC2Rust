"""Deprecated test shim – real tests live in ``tests/test_memory.py``."""

import pytest


from llm.memory import (
    NoOpStrategy,
    SlidingWindowStrategy,
    SummaryStrategy,
    TokenLimitStrategy,
    create_memory_strategy,
)


def _make_messages(include_system: bool = True, count: int = 6):
    messages = []
    if include_system:
        messages.append({"role": "system", "content": "system"})
    for idx in range(count):
        role = "user" if idx % 2 == 0 else "assistant"
        messages.append({"role": role, "content": f"message-{idx}"})
    return messages


def test_sliding_window_strategy_keeps_recent_messages():
    strategy = SlidingWindowStrategy(max_messages=2)
    messages = _make_messages(include_system=True, count=3)

    trimmed = strategy.process(messages)

    assert len(trimmed) == 3
    assert trimmed[0]["role"] == "system"
    # 只保留最近的两条非系统消息
    assert [m["content"] for m in trimmed[1:]] == ["message-1", "message-2"]


def test_memory_str_input_is_normalised():
    strategy = TokenLimitStrategy(max_tokens=100)
    raw_messages = ["工具调用输出A", "工具调用输出B"]

    trimmed = strategy.process(raw_messages)

    assert all(isinstance(m, dict) for m in trimmed)
    assert [m["content"] for m in trimmed] == raw_messages
    assert all(m["role"] == "assistant" for m in trimmed)


def test_token_limit_strategy_respects_budget():
    strategy = TokenLimitStrategy(max_tokens=5)
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "aaaa"},
        {"role": "assistant", "content": "bbbbbbbb"},
        {"role": "user", "content": "cccccccc"},
    ]

    trimmed = strategy.process(messages)

    assert len(trimmed) == 3
    assert trimmed[0]["role"] == "system"
    assert [m["role"] for m in trimmed[1:]] == ["assistant", "user"]


def test_summary_strategy_inserts_summary():
    calls = []

    def fake_summarizer(prompt: str) -> str:
        calls.append(prompt)
        return "简要摘要"

    strategy = SummaryStrategy(
        summarizer=fake_summarizer,
        keep_recent=2,
        checkpoint_interval=2,
        summary_max_tokens=200,
    )
    messages = _make_messages(include_system=True, count=5)

    trimmed = strategy.process(messages)

    assert len(calls) == 1
    # 应包含系统摘要消息
    summary_messages = [m for m in trimmed if m["role"] == "system" and "摘要" in m["content"]]
    assert summary_messages, "expected summary system message"
    # 保留最近两条消息
    assert [m["content"] for m in trimmed[-2:]] == ["message-3", "message-4"]


def test_create_memory_strategy_factory():
    assert isinstance(create_memory_strategy("noop"), NoOpStrategy)
    assert isinstance(
        create_memory_strategy({"name": "sliding_window", "max_messages": 3}),
        SlidingWindowStrategy,
    )

    strategy = create_memory_strategy(
        {"name": "summary", "keep_recent": 1}, summarizer=lambda _: "summary"
    )
    assert isinstance(strategy, SummaryStrategy)

    with pytest.raises(ValueError):
        create_memory_strategy({"name": "summary"})