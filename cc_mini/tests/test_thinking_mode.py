import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from cc_mini.config import load_app_config
from cc_mini.engine import Engine
from cc_mini.llm import (
    LLMMessage,
    LLMThinkingConfig,
    ReasoningLengthEmptyError,
    _build_openai_request,
    _normalize_openai_message,
    _to_openai_messages,
    _OpenAIStream,
)
from cc_mini.permissions import PermissionChecker
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


class ThinkingConfigTest(unittest.TestCase):
    def test_thinking_defaults_enabled_for_primary_and_fallback(self):
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
model = "fallback-model"
""".lstrip(),
                encoding="utf-8",
            )

            config = load_app_config(_config_args(config=str(path)))

            self.assertTrue(config.thinking.enabled)
            self.assertIsNotNone(config.fallback)
            self.assertTrue(config.fallback.thinking.enabled)

    def test_thinking_can_be_disabled_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".cc-mini.toml"
            path.write_text(
                """
provider = "openai"
api_key = "primary-key"
base_url = "https://primary.example/v1"
model = "primary-model"

[thinking]
enabled = false

[fallback]
enabled = true
provider = "openai"
model = "fallback-model"

[fallback.thinking]
enabled = false
""".lstrip(),
                encoding="utf-8",
            )

            config = load_app_config(_config_args(config=str(path)))

            self.assertFalse(config.thinking.enabled)
            self.assertIsNotNone(config.fallback)
            self.assertFalse(config.fallback.thinking.enabled)


class ThinkingRequestTest(unittest.TestCase):
    def test_deepseek_style_thinking_overrides_openai_extra_body(self):
        request = _build_openai_request(
            model="deepseek/deepseek-v4-pro",
            max_tokens=8192,
            system=None,
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
            effort=None,
            openai_extra_body={
                "thinking": {"type": "disabled"},
                "enable_thinking": False,
                "other": "kept",
            },
            thinking=LLMThinkingConfig(enabled=True),
            base_url="https://api.ppio.com/openai",
            stream=False,
        )

        self.assertEqual(
            request["extra_body"],
            {"other": "kept", "thinking": {"type": "enabled"}},
        )

    def test_dashscope_uses_enable_thinking(self):
        request = _build_openai_request(
            model="deepseek-v4-pro",
            max_tokens=8192,
            system=None,
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
            effort=None,
            openai_extra_body={"thinking": {"type": "disabled"}, "other": "kept"},
            thinking=LLMThinkingConfig(enabled=True),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            stream=False,
        )

        self.assertEqual(
            request["extra_body"],
            {"other": "kept", "enable_thinking": True},
        )

    def test_openai_create_message_accepts_base_url_and_applies_thinking(self):
        created = {}

        class _Completions:
            def create(self, **kwargs):
                created.update(kwargs)

                class _Response:
                    choices = [
                        type(
                            "Choice",
                            (),
                            {
                                "message": {
                                    "content": "ok",
                                    "tool_calls": [],
                                },
                                "finish_reason": "stop",
                            },
                        )()
                    ]
                    usage = None

                return _Response()

        class _Client:
            chat = type("Chat", (), {"completions": _Completions()})()

        client = object.__new__(__import__("cc_mini.llm", fromlist=["LLMClient"]).LLMClient)
        response = client._openai_create_message(
            client=_Client(),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="deepseek-v4-pro",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system=None,
            tools=[],
            effort=None,
            openai_extra_body=None,
            thinking=LLMThinkingConfig(enabled=True),
        )

        self.assertEqual(response.content, [{"type": "text", "text": "ok"}])
        self.assertEqual(created["extra_body"], {"enable_thinking": True})


class ThinkingMessageTest(unittest.TestCase):
    def test_reasoning_is_preserved_with_tool_calls_when_enabled(self):
        message = {
            "content": None,
            "reasoning_content": "Need to inspect files.",
            "reasoning_details": [{"type": "reasoning.text", "text": "detail"}],
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "Read",
                        "arguments": '{"file_path": "src/lib.rs"}',
                    },
                }
            ],
        }

        blocks = _normalize_openai_message(message, preserve_reasoning=True)
        self.assertEqual(blocks[0], {"type": "reasoning", "text": "Need to inspect files."})
        self.assertEqual(blocks[1]["type"], "reasoning_details")
        self.assertEqual(blocks[2]["type"], "tool_use")

        out = _to_openai_messages(None, [{"role": "assistant", "content": blocks}])
        self.assertEqual(out[0]["reasoning_content"], "Need to inspect files.")
        self.assertEqual(out[0]["reasoning_details"], [{"type": "reasoning.text", "text": "detail"}])
        self.assertEqual(out[0]["tool_calls"][0]["id"], "call-1")

    def test_reasoning_is_dropped_when_disabled(self):
        message = {
            "content": None,
            "reasoning_content": "Need to inspect files.",
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "Read", "arguments": "{}"},
                }
            ],
        }

        blocks = _normalize_openai_message(message, preserve_reasoning=False)
        self.assertEqual([block["type"] for block in blocks], ["tool_use"])

    def test_final_answer_does_not_force_reasoning_replay(self):
        message = {
            "content": "done",
            "reasoning_content": "No tool required.",
            "tool_calls": [],
        }

        blocks = _normalize_openai_message(message, preserve_reasoning=True)
        self.assertEqual(blocks, [{"type": "text", "text": "done"}])


class _FakeCompletions:
    def __init__(self, chunks):
        self._chunks = chunks

    def create(self, **kwargs):
        return iter(self._chunks)


class _FakeChat:
    def __init__(self, chunks):
        self.completions = _FakeCompletions(chunks)


class _FakeOpenAIClient:
    def __init__(self, chunks):
        self.chat = _FakeChat(chunks)


class ThinkingStreamTest(unittest.TestCase):
    def test_stream_accumulates_reasoning_and_tool_calls(self):
        chunks = [
            {
                "choices": [
                    {
                        "delta": {
                            "reasoning_content": "Need tool.",
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "call-1",
                                    "function": {
                                        "name": "Bash",
                                        "arguments": '{"command": "cargo test"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ]
        stream = _OpenAIStream(
            client=_FakeOpenAIClient(chunks),
            model="deepseek/deepseek-v4-pro",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system=None,
            tools=[],
            effort=None,
            openai_extra_body=None,
            thinking=LLMThinkingConfig(enabled=True),
        )

        with stream as active:
            list(active.text_stream)
            final = active.get_final_message()

        self.assertEqual(final.content[0], {"type": "reasoning", "text": "Need tool."})
        self.assertEqual(final.content[1]["type"], "tool_use")
        out = _to_openai_messages(None, [{"role": "assistant", "content": final.content}])
        self.assertEqual(out[0]["reasoning_content"], "Need tool.")

    def test_stream_reasoning_length_empty_is_classified(self):
        chunks = [
            {
                "choices": [
                    {
                        "finish_reason": "length",
                        "delta": {
                            "reasoning_content": "Long reasoning without answer.",
                        },
                    }
                ]
            }
        ]
        records = []
        stream = _OpenAIStream(
            client=_FakeOpenAIClient(chunks),
            model="deepseek/deepseek-v4-pro",
            max_tokens=8192,
            messages=[{"role": "user", "content": "hi"}],
            system=None,
            tools=[],
            effort=None,
            openai_extra_body=None,
            thinking=LLMThinkingConfig(enabled=True),
            response_logger=lambda direction, payload: records.append((direction, payload)),
        )

        with self.assertRaises(ReasoningLengthEmptyError):
            with stream as active:
                list(active.text_stream)
                active.get_final_message()

        self.assertEqual(records[0][0], "reasoning_length_empty")

    def test_reasoning_is_rendered_in_raw_text(self):
        from cc_mini.llm import _blocks_to_text

        rendered = _blocks_to_text([
            {"type": "reasoning", "text": "private reasoning"},
            {"type": "reasoning_details", "details": [{"text": "detail"}]},
            {"type": "tool_use", "id": "1", "name": "Bash", "input": {"command": "pwd"}},
        ])

        self.assertIn("[reasoning]\nprivate reasoning", rendered)
        self.assertIn("[reasoning_details]\n", rendered)
        self.assertIn("detail", rendered)


class ThinkingEmptyOutputTest(unittest.TestCase):
    def test_reasoning_length_empty_is_classified(self):
        from cc_mini.llm import LLMClient

        client = LLMClient(
            provider="openai",
            api_key="primary-key",
            thinking=LLMThinkingConfig(enabled=True),
        )

        with self.assertRaises(ReasoningLengthEmptyError):
            client._validate_non_empty_response(
                LLMMessage(
                    content=[],
                    raw_summary={
                        "choices": [
                            {
                                "finish_reason": "length",
                                "content_len": 0,
                                "tool_calls_count": 0,
                                "reasoning_content_present": True,
                            }
                        ]
                    },
                ),
                provider="openai",
                model="deepseek/deepseek-v4-pro",
            )


class _ReasoningLengthClient:
    has_fallback = False

    def __init__(self, failures_before_success: int = 1):
        self.calls = []
        self.failures_before_success = failures_before_success

    def create_message(self, **kwargs):
        self.calls.append(kwargs["messages"])
        if len(self.calls) <= self.failures_before_success:
            raise ReasoningLengthEmptyError("reasoning_length_empty")
        return LLMMessage(
            content=[
                {"type": "tool_use", "id": "finish-1", "name": "finish", "input": {"final_answer": "done"}},
            ]
        )

    def stream_messages(self, **kwargs):
        raise AssertionError("stream should not be used")

    def consume_status_events(self):
        return []

    @staticmethod
    def error_message(exc):
        return str(exc)

    @staticmethod
    def is_reasoning_length_empty_error(exc):
        return isinstance(exc, ReasoningLengthEmptyError)

    @staticmethod
    def is_authentication_error(exc):
        return False

    @staticmethod
    def is_retryable_error(exc):
        return False

    @staticmethod
    def is_api_error(exc):
        return False


class ThinkingEngineRetryTest(unittest.TestCase):
    def test_reasoning_length_empty_adds_recovery_signal_and_retries_with_budget(self):
        engine = Engine(
            tools=[FinishTool()],
            system_prompt="system",
            permission_checker=PermissionChecker(auto_approve=True),
            provider="openai",
            api_key="primary-key",
            model="deepseek/deepseek-v4-pro",
            stream=False,
        )
        client = _ReasoningLengthClient(failures_before_success=2)
        engine._client = client

        events = list(engine.submit("hi"))

        self.assertEqual(len(client.calls), 3)
        self.assertTrue(any(event[0] == "error" and "recovery signal" in event[1] for event in events))
        self.assertTrue(any(event[0] == "error" and "reasoning_length_empty, retrying" in event[1] for event in events))
        self.assertIn(("text", "done\n"), events)
        recovery_messages = client.calls[1]
        self.assertTrue(
            any(
                isinstance(message.get("content"), str)
                and "只输出了 reasoning" in message.get("content", "")
                for message in recovery_messages
            )
        )


class _ReasoningClient:
    has_fallback = False

    def create_message(self, **kwargs):
        return LLMMessage(
            content=[
                {"type": "reasoning", "text": "Need to run tests."},
                {"type": "tool_use", "id": "finish-1", "name": "finish", "input": {"final_answer": "done"}},
            ]
        )

    def stream_messages(self, **kwargs):
        raise AssertionError("stream should not be used")

    def consume_status_events(self):
        return []

    @staticmethod
    def error_message(exc):
        return str(exc)

    @staticmethod
    def is_reasoning_length_empty_error(exc):
        return False

    @staticmethod
    def is_authentication_error(exc):
        return False

    @staticmethod
    def is_retryable_error(exc):
        return False

    @staticmethod
    def is_api_error(exc):
        return False


class ThinkingEventTest(unittest.TestCase):
    def test_engine_yields_reasoning_before_tool_use(self):
        engine = Engine(
            tools=[FinishTool()],
            system_prompt="system",
            permission_checker=PermissionChecker(auto_approve=True),
            provider="openai",
            api_key="primary-key",
            stream=False,
        )
        engine._client = _ReasoningClient()

        events = list(engine.submit("hi"))

        self.assertIn(("reasoning", "Need to run tests."), events)
        self.assertIn(("text", "done\n"), events)
