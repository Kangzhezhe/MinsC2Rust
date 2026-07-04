import json
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import cc_mini.engine as engine_mod
from cc_mini.config import load_app_config
from cc_mini.engine import Engine
from cc_mini.llm import (
    LLMClient,
    LLMFallbackConfig,
    LLMMessage,
    LLMThinkingConfig,
    ReasoningLengthEmptyError,
    UpstreamEmptyOutputError,
    _build_openai_request,
)
from cc_mini.permissions import PermissionChecker
from cc_mini.tools.base import Tool, ToolResult
from cc_mini.tools.finish import FinishTool


def _config_args(**overrides):
    values = dict(
        prompt=None,
        print=False,
        auto_approve=True,
        config=None,
        provider=None,
        api_key=None,
        base_url=None,
        model=None,
        max_tokens=None,
        effort=None,
        stream=None,
        resume=None,
        memory_dir=None,
        no_auto_dream=False,
        dream_interval=None,
        dream_min_sessions=None,
        coordinator=False,
    )
    values.update(overrides)
    return Namespace(**values)


class _NoopTool(Tool):
    @property
    def name(self):
        return "noop"

    @property
    def description(self):
        return "noop"

    @property
    def input_schema(self):
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs):
        return ToolResult(content="ok")


class FallbackConfigTest(unittest.TestCase):
    def test_loads_simple_fallback_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".cc-mini.toml"
            path.write_text(
                """
provider = "openai"
api_key = "primary-key"
base_url = "https://primary.example/v1"
model = "primary-model"

[fallback]
enabled = true
provider = "openai"
api_key = "fallback-key"
base_url = "https://fallback.example/v1"
model = "fallback-model"
""".lstrip(),
                encoding="utf-8",
            )

            config = load_app_config(_config_args(config=str(path)))

            self.assertIsNotNone(config.fallback)
            self.assertTrue(config.fallback.enabled)
            self.assertEqual(config.fallback.provider, "openai")
            self.assertEqual(config.fallback.api_key, "fallback-key")
            self.assertEqual(config.fallback.base_url, "https://fallback.example/v1")
            self.assertEqual(config.fallback.model, "fallback-model")

    def test_loads_primary_and_fallback_openai_extra_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".cc-mini.toml"
            path.write_text(
                """
provider = "openai"
api_key = "primary-key"
base_url = "https://primary.example/v1"
model = "primary-model"

[openai_extra_body]
enable_thinking = false

[fallback]
enabled = true
provider = "openai"
api_key = "fallback-key"
base_url = "https://fallback.example/v1"
model = "fallback-model"

[fallback.openai_extra_body]
enable_thinking = false
""".lstrip(),
                encoding="utf-8",
            )

            config = load_app_config(_config_args(config=str(path)))

            self.assertEqual(config.openai_extra_body, {"enable_thinking": False})
            self.assertIsNotNone(config.fallback)
            self.assertEqual(config.fallback.openai_extra_body, {"enable_thinking": False})


class LLMClientFallbackTest(unittest.TestCase):
    def test_build_openai_request_includes_extra_body(self):
        request = _build_openai_request(
            model="deepseek-v4-pro",
            max_tokens=8192,
            system="system",
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
            effort=None,
            openai_extra_body={"enable_thinking": False},
            stream=False,
        )

        self.assertEqual(request["extra_body"], {"enable_thinking": False})

    def test_create_message_uses_fallback_after_primary_exception(self):
        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            fallback=LLMFallbackConfig(
                enabled=True,
                provider="openai",
                api_key="fallback-key",
                base_url="https://fallback.example/v1",
                model="fallback-model",
            ),
        )
        calls = []

        def fake_create_once(**kwargs):
            calls.append((kwargs["provider"], kwargs["model"]))
            if len(calls) == 1:
                raise RuntimeError("primary failed")
            return LLMMessage(content=[{"type": "tool_use", "id": "1", "name": "noop", "input": {}}])

        client._create_message_once = fake_create_once
        client._fallback_client = object()

        response = client.create_message(
            model="primary-model",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system="system",
            tools=[],
        )

        self.assertEqual(calls, [("openai", "primary-model"), ("openai", "fallback-model")])
        self.assertTrue(response.fallback_used)
        self.assertEqual(response.model, "fallback-model")
        events = "\n".join(client.consume_status_events())
        self.assertIn("primary failed", events)
        self.assertIn("fallback succeeded", events)

    def test_create_message_uses_fallback_after_empty_content(self):
        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            fallback=LLMFallbackConfig(enabled=True, provider="openai", model="fallback-model"),
        )
        calls = []

        def fake_create_once(**kwargs):
            calls.append((kwargs["provider"], kwargs["model"]))
            if len(calls) == 1:
                return LLMMessage(content=[])
            return LLMMessage(content=[{"type": "tool_use", "id": "1", "name": "noop", "input": {}}])

        client._create_message_once = fake_create_once
        client._fallback_client = object()

        response = client.create_message(
            model="primary-model",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system="system",
            tools=[],
        )

        self.assertEqual(calls, [("openai", "primary-model"), ("openai", "fallback-model")])
        self.assertTrue(response.fallback_used)

    def test_create_message_applies_default_thinking_to_primary_and_fallback_extra_body(self):
        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            openai_extra_body={"thinking": {"type": "disabled"}},
            fallback=LLMFallbackConfig(
                enabled=True,
                provider="openai",
                model="fallback-model",
                openai_extra_body={"enable_thinking": False},
            ),
        )
        calls = []

        def fake_create_once(**kwargs):
            calls.append((kwargs["provider"], kwargs["model"], kwargs["openai_extra_body"]))
            if len(calls) == 1:
                raise RuntimeError("primary failed")
            return LLMMessage(content=[{"type": "tool_use", "id": "1", "name": "noop", "input": {}}])

        client._create_message_once = fake_create_once
        client._fallback_client = object()

        response = client.create_message(
            model="primary-model",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system="system",
            tools=[],
        )

        self.assertTrue(response.fallback_used)
        self.assertEqual(
            calls,
            [
                ("openai", "primary-model", {"thinking": {"type": "enabled"}}),
                ("openai", "fallback-model", {"thinking": {"type": "enabled"}}),
            ],
        )

    def test_create_message_can_disable_thinking_for_primary_and_fallback(self):
        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            openai_extra_body={"thinking": {"type": "enabled"}},
            thinking=LLMThinkingConfig(enabled=False),
            fallback=LLMFallbackConfig(
                enabled=True,
                provider="openai",
                model="fallback-model",
                openai_extra_body={"enable_thinking": True},
                thinking=LLMThinkingConfig(enabled=False),
            ),
        )
        calls = []

        def fake_create_once(**kwargs):
            calls.append((kwargs["provider"], kwargs["model"], kwargs["openai_extra_body"]))
            if len(calls) == 1:
                raise RuntimeError("primary failed")
            return LLMMessage(content=[{"type": "tool_use", "id": "1", "name": "noop", "input": {}}])

        client._create_message_once = fake_create_once
        client._fallback_client = object()

        response = client.create_message(
            model="primary-model",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system="system",
            tools=[],
        )

        self.assertTrue(response.fallback_used)
        self.assertEqual(
            calls,
            [
                ("openai", "primary-model", {"thinking": {"type": "disabled"}}),
                ("openai", "fallback-model", {"thinking": {"type": "disabled"}}),
            ],
        )

    def test_fallback_thinking_uses_fallback_dashscope_base_url(self):
        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            base_url="https://api.ppio.com/openai",
            fallback=LLMFallbackConfig(
                enabled=True,
                provider="openai",
                model="fallback-model",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
        )
        calls = []

        def fake_create_once(**kwargs):
            calls.append((kwargs["provider"], kwargs["model"], kwargs["base_url"], kwargs["openai_extra_body"]))
            if len(calls) == 1:
                raise RuntimeError("primary failed")
            return LLMMessage(content=[{"type": "tool_use", "id": "1", "name": "noop", "input": {}}])

        client._create_message_once = fake_create_once
        client._fallback_client = object()

        response = client.create_message(
            model="primary-model",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system="system",
            tools=[],
        )

        self.assertTrue(response.fallback_used)
        self.assertEqual(
            calls,
            [
                (
                    "openai",
                    "primary-model",
                    "https://api.ppio.com/openai",
                    {"thinking": {"type": "enabled"}},
                ),
                (
                    "openai",
                    "fallback-model",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    {"enable_thinking": True},
                ),
            ],
        )

    def test_reasoning_length_empty_does_not_trigger_fallback(self):
        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            fallback=LLMFallbackConfig(
                enabled=True,
                provider="openai",
                model="fallback-model",
            ),
        )
        calls = []

        def fake_create_once(**kwargs):
            calls.append((kwargs["provider"], kwargs["model"]))
            raise ReasoningLengthEmptyError("reasoning_length_empty")

        client._create_message_once = fake_create_once
        client._fallback_client = object()

        with self.assertRaises(ReasoningLengthEmptyError):
            client.create_message(
                model="primary-model",
                max_tokens=8192,
                messages=[{"role": "user", "content": "hi"}],
                system="system",
                tools=[],
            )

        self.assertEqual(calls, [("openai", "primary-model")])

    def test_primary_empty_response_logs_raw_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "llm.jsonl"
            with patch.dict(os.environ, {"CC_MINI_LLM_LOG_FILE": str(log_path)}, clear=False):
                client = LLMClient(provider="openai", api_key="primary-key")

            client._create_message_once = lambda **_: LLMMessage(
                content=[],
                raw_summary={
                    "choice_count": 1,
                    "choices": [
                        {
                            "finish_reason": "length",
                            "content_is_none": True,
                            "tool_calls_count": 0,
                            "reasoning_content_present": True,
                        }
                    ],
                },
            )

            with self.assertRaises(ReasoningLengthEmptyError):
                client.create_message(
                    model="primary-model",
                    max_tokens=8192,
                    messages=[{"role": "user", "content": "hi"}],
                    system="system",
                    tools=[],
                )

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            empty_records = [r for r in records if r.get("direction") == "reasoning_length_empty"]
            self.assertEqual(len(empty_records), 1)
            payload = empty_records[0]["payload"]
            self.assertEqual(payload["provider"], "openai")
            self.assertEqual(payload["model"], "primary-model")
            self.assertFalse(payload["fallback"])
            self.assertEqual(payload["raw_summary"]["choices"][0]["finish_reason"], "length")
            self.assertTrue(payload["raw_summary"]["choices"][0]["reasoning_content_present"])

    def test_fallback_empty_response_logs_raw_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "llm.jsonl"
            with patch.dict(os.environ, {"CC_MINI_LLM_LOG_FILE": str(log_path)}, clear=False):
                client = LLMClient(
                    provider="openai",
                    api_key="primary-key",
                    fallback=LLMFallbackConfig(enabled=True, provider="openai", model="fallback-model"),
                )
            calls = []

            def fake_create_once(**kwargs):
                calls.append((kwargs["provider"], kwargs["model"]))
                if len(calls) == 1:
                    raise RuntimeError("primary failed")
                return LLMMessage(
                    content=[],
                    raw_summary={
                        "choice_count": 1,
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "content_is_none": True,
                                "tool_calls_count": 0,
                            }
                        ],
                    },
                )

            client._create_message_once = fake_create_once
            client._fallback_client = object()

            with self.assertRaises(RuntimeError):
                client.create_message(
                    model="primary-model",
                    max_tokens=8192,
                    messages=[{"role": "user", "content": "hi"}],
                    system="system",
                    tools=[],
                )

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            empty_records = [r for r in records if r.get("direction") == "fallback_empty_response"]
            self.assertEqual(len(empty_records), 1)
            payload = empty_records[0]["payload"]
            self.assertEqual(payload["provider"], "openai")
            self.assertEqual(payload["model"], "fallback-model")
            self.assertTrue(payload["fallback"])
            self.assertEqual(payload["raw_summary"]["choices"][0]["finish_reason"], "stop")


class _NoToolThenFallbackClient:
    has_fallback = True

    def __init__(self):
        self.primary_calls = 0
        self.fallback_calls = 0
        self.status_events = []

    def create_message(self, **kwargs):
        if kwargs.get("fallback_only"):
            self.fallback_calls += 1
            self.status_events.append("[CC-MINI-FALLBACK] fallback succeeded provider=openai model=fallback")
            return LLMMessage(
                content=[
                    {
                        "type": "tool_use",
                        "id": "finish-1",
                        "name": "finish",
                        "input": {"final_answer": "done"},
                    }
                ],
                model="fallback",
                fallback_used=True,
            )
        self.primary_calls += 1
        return LLMMessage(content=[{"type": "text", "text": "plain text"}])

    def stream_messages(self, **kwargs):
        raise AssertionError("stream should not be used")

    def consume_status_events(self):
        events = list(self.status_events)
        self.status_events.clear()
        return events

    def error_message(self, exc):
        return str(exc)

    def is_authentication_error(self, exc):
        return False

    def is_retryable_error(self, exc):
        return False

    def is_api_error(self, exc):
        return False


class EngineFallbackTest(unittest.TestCase):
    def test_no_tool_retries_exhausted_uses_fallback_once(self):
        original_max_retries = engine_mod._MAX_RETRIES
        original_backoff = engine_mod._RETRY_BACKOFF
        engine_mod._MAX_RETRIES = 2
        engine_mod._RETRY_BACKOFF = (0, 0)
        try:
            engine = Engine(
                tools=[_NoopTool(), FinishTool()],
                system_prompt="system",
                permission_checker=PermissionChecker(auto_approve=True),
            )
            client = _NoToolThenFallbackClient()
            engine._client = client

            events = list(engine.submit("hello"))

            self.assertEqual(client.primary_calls, 3)
            self.assertEqual(client.fallback_calls, 1)
            self.assertIn(("text", "done\n"), events)
            self.assertTrue(any(e[0] == "error" and "no tools called retries exhausted" in e[1] for e in events))
        finally:
            engine_mod._MAX_RETRIES = original_max_retries
            engine_mod._RETRY_BACKOFF = original_backoff


if __name__ == "__main__":
    unittest.main()
