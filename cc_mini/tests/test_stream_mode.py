import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from cc_mini.config import load_app_config
from cc_mini.engine import Engine
from cc_mini.llm import LLMMessage
from cc_mini.permissions import PermissionChecker
from cc_mini.tools.base import Tool, ToolResult


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
        raise AssertionError("tool should not run")


class _FakeClient:
    def __init__(self):
        self.create_calls = 0
        self.stream_calls = 0

    def create_message(self, **kwargs):
        self.create_calls += 1
        return LLMMessage(content=[{"type": "text", "text": "done"}])

    def stream_messages(self, **kwargs):
        self.stream_calls += 1
        raise AssertionError("stream_messages should not be used")

    def error_message(self, exc):
        return str(exc)

    def is_authentication_error(self, exc):
        return False

    def is_retryable_error(self, exc):
        return False

    def is_api_error(self, exc):
        return False


class _FakeStream:
    def __enter__(self):
        self.text_stream = iter(["streamed"])
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def close(self):
        pass

    def get_final_message(self):
        return LLMMessage(content=[{"type": "text", "text": "streamed"}])


class _StreamingFakeClient(_FakeClient):
    def create_message(self, **kwargs):
        raise AssertionError("create_message should not be used")

    def stream_messages(self, **kwargs):
        self.stream_calls += 1
        return _FakeStream()


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


class StreamModeConfigTest(unittest.TestCase):
    def test_stream_defaults_to_false(self):
        config = load_app_config(_config_args())
        self.assertFalse(config.stream)

    def test_stream_can_be_enabled_from_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cc-mini.toml"
            path.write_text("stream = true\n", encoding="utf-8")
            config = load_app_config(_config_args(config=str(path)))
            self.assertTrue(config.stream)

    def test_stream_can_be_enabled_from_cli(self):
        config = load_app_config(_config_args(stream=True))
        self.assertTrue(config.stream)


class StreamModeEngineTest(unittest.TestCase):
    def test_engine_uses_non_streaming_client_by_default(self):
        engine = Engine(
            tools=[_NoopTool()],
            system_prompt="system",
            permission_checker=PermissionChecker(auto_approve=True),
        )
        client = _FakeClient()
        engine._client = client

        events = list(engine.submit("hello"))

        self.assertEqual(client.create_calls, 1)
        self.assertEqual(client.stream_calls, 0)
        self.assertIn(("text", "done"), events)

    def test_engine_uses_streaming_client_when_enabled(self):
        engine = Engine(
            tools=[_NoopTool()],
            system_prompt="system",
            permission_checker=PermissionChecker(auto_approve=True),
            stream=True,
        )
        client = _StreamingFakeClient()
        engine._client = client

        events = list(engine.submit("hello"))

        self.assertEqual(client.create_calls, 0)
        self.assertEqual(client.stream_calls, 1)
        self.assertIn(("text", "streamed"), events)


if __name__ == "__main__":
    unittest.main()
