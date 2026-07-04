import unittest

from cc_mini import CCMini
from cc_mini.engine import Engine
from cc_mini.llm import LLMClient


class _Closeable:
    def __init__(self):
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


class CloseLifecycleTest(unittest.TestCase):
    def test_llm_client_closes_primary_and_fallback_clients(self):
        primary = _Closeable()
        fallback = _Closeable()
        client = LLMClient.__new__(LLMClient)
        client._client = primary
        client._fallback_client = fallback

        client.close()

        self.assertEqual(primary.close_calls, 1)
        self.assertEqual(fallback.close_calls, 1)
        self.assertIsNone(client._fallback_client)

    def test_engine_close_closes_active_stream_and_client(self):
        stream = _Closeable()
        client = _Closeable()
        engine = Engine.__new__(Engine)
        engine._active_stream = stream
        engine._client = client
        engine._aborted = False

        engine.close()

        self.assertEqual(stream.close_calls, 1)
        self.assertEqual(client.close_calls, 1)
        self.assertIsNone(engine._active_stream)

    def test_ccmini_close_closes_engine(self):
        engine = _Closeable()
        cc_mini = CCMini.__new__(CCMini)
        cc_mini.engine = engine

        cc_mini.close()

        self.assertEqual(engine.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
