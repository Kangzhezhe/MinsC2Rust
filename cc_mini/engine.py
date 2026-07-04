from __future__ import annotations
import time
from typing import TYPE_CHECKING, Any, Iterator
from .config import DEFAULT_MODEL, default_max_tokens_for_model, resolve_model
from .llm import LLMClient, LLMFallbackConfig, LLMThinkingConfig
from .tools.base import Tool, ToolResult
from .permissions import PermissionChecker
from .shared_logger import get_ccmini_logger

if TYPE_CHECKING:
    from .cost_tracker import CostTracker
    from .session import SessionStore

_MAX_RETRIES = 5
_RETRY_BACKOFF = (1, 3, 5, 10, 30)

# Guardrail for tool outputs appended into conversation context.
# Prevents very large tool responses from blowing up token usage.
_TOOL_RESULT_MAX_CHARS = 20000 * 4

_logger = get_ccmini_logger()


class AbortedError(Exception):
    """Raised when the current turn is aborted by the user (Esc / Ctrl+C)."""


def _normalize_content_block(block: Any) -> dict[str, Any]:
    """Convert SDK content blocks into plain API dictionaries.

    Anthropic-compatible backends can reject SDK-specific object fields that
    are harmless against Anthropic's own endpoint, so only persist the wire
    fields we actually want to send back.
    """
    if isinstance(block, dict):
        normalized = dict(block)
    else:
        normalized = {}
        for field in (
            "type", "text", "id", "name", "input", "tool_use_id",
            "content", "is_error", "source",
        ):
            if hasattr(block, field):
                normalized[field] = getattr(block, field)

    block_type = normalized.get("type")
    if block_type == "text":
        return {"type": "text", "text": normalized.get("text", "")}
    if block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": normalized.get("id", ""),
            "name": normalized.get("name", ""),
            "input": _normalize_json_value(normalized.get("input", {})),
        }
    if block_type == "tool_result":
        result = {
            "type": "tool_result",
            "tool_use_id": normalized.get("tool_use_id", ""),
            "content": _normalize_json_value(normalized.get("content", "")),
        }
        if "is_error" in normalized:
            result["is_error"] = bool(normalized["is_error"])
        return result
    if block_type == "image":
        return {
            "type": "image",
            "source": _normalize_json_value(normalized.get("source", {})),
        }
    return {
        key: _normalize_json_value(value)
        for key, value in normalized.items()
        if value is not None
    }


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _normalize_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(item) for item in value]
    if hasattr(value, "model_dump"):
        return _normalize_json_value(value.model_dump())
    if hasattr(value, "dict"):
        return _normalize_json_value(value.dict())
    if hasattr(value, "__dict__"):
        data = {
            key: val for key, val in vars(value).items()
            if not key.startswith("_") and not callable(val)
        }
        if data:
            return _normalize_json_value(data)
    return value


def _normalize_message_content(content: Any) -> Any:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return [_normalize_content_block(block) for block in content]
    return _normalize_json_value(content)


def _truncate_tool_result_text(text: str, max_chars: int = _TOOL_RESULT_MAX_CHARS) -> str:
    raw = str(text or "")
    truncated_by_chars = False
    if len(raw) > max_chars:
        raw = raw[:max_chars]
        truncated_by_chars = True

    if truncated_by_chars:
        suffix = (
            "\n\n[TOOL_OUTPUT_TRUNCATED] "
            f"limits=chars:{max_chars}; "
            f"truncated_by_chars={truncated_by_chars}"
        )
        return raw.rstrip() + suffix
    return raw


class Engine:
    def __init__(self, tools: list[Tool], system_prompt: str,
                 permission_checker: PermissionChecker,
                 provider: str = "anthropic",
                 model: str = DEFAULT_MODEL,
                 max_tokens: int | None = None,
                 api_key: str | None = None,
                 base_url: str | None = None,
                 effort: str | None = None,
                 openai_extra_body: dict | None = None,
                 thinking: LLMThinkingConfig | None = None,
                 stream: bool = False,
                 fallback: LLMFallbackConfig | None = None,
                 session_store: SessionStore | None = None,
                 cost_tracker: CostTracker | None = None):
        self._provider = provider
        self._model = resolve_model(model, provider=provider)
        self._max_tokens = max_tokens or default_max_tokens_for_model(
            self._model,
            provider=provider,
        )
        self._effort = effort
        self._stream = bool(stream)
        self._client = LLMClient(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            openai_extra_body=openai_extra_body,
            thinking=thinking,
            fallback=fallback,
        )
        self._tools = {t.name: t for t in tools}
        self._system_prompt = system_prompt
        self._permissions = permission_checker
        self._messages: list[dict] = []
        self._aborted = False
        self._turn_start_len: int | None = None
        self._active_stream = None  # reference to current HTTP stream
        self._session_store = session_store
        self._cost_tracker = cost_tracker

    # -- message accessors (for compact / resume / commands) ----------------

    def get_messages(self) -> list[dict]:
        return list(self._messages)

    def set_messages(self, messages: list[dict]) -> None:
        self._messages = [
            {
                "role": message["role"],
                "content": _normalize_message_content(message.get("content", "")),
            }
            for message in messages
        ]

    def get_system_prompt(self) -> str:
        return self._system_prompt

    def set_session_store(self, store: SessionStore | None) -> None:
        self._session_store = store

    def set_tools(self, tools: list[Tool]) -> None:
        self._tools = {t.name: t for t in tools}

    def get_model(self) -> str:
        return self._model

    def set_model(self, model: str) -> None:
        self._model = resolve_model(model, provider=self._provider)
        self._max_tokens = default_max_tokens_for_model(
            self._model,
            provider=self._provider,
        )

    def _persist(self, message: dict) -> None:
        """Append message to session store if available."""
        if self._session_store is not None:
            try:
                self._session_store.append_message(message)
            except Exception:
                pass  # don't break the conversation on I/O errors

    @property
    def messages(self) -> list[dict]:
        return self._messages

    @messages.setter
    def messages(self, value: list[dict]) -> None:
        self._messages = value

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, value: str) -> None:
        self._system_prompt = value

    def last_assistant_text(self) -> str:
        """Extract text from the last assistant message."""
        if not self._messages:
            return ""
        last = self._messages[-1]
        if last.get("role") != "assistant":
            return ""
        content = last.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if hasattr(block, "text"):
                    parts.append(block.text)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "".join(parts)
        return ""

    def abort(self):
        """Abort the current turn immediately.

        Matches claude-code-main's AbortController.abort(): sets flag and
        closes the active HTTP stream so the generator unblocks at once.
        """
        self._aborted = True
        if self._active_stream is not None:
            try:
                self._active_stream.close()
            except Exception:
                pass

    def close(self) -> None:
        if self._active_stream is not None:
            try:
                self._active_stream.close()
            except Exception:
                pass
            self._active_stream = None

        close = getattr(self._client, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    def cancel_turn(self):
        """Roll back messages to the state before the current turn started.

        Uses _turn_start_len (set at the beginning of submit()) to restore
        messages to the exact state before the turn. This is more robust than
        trying to walk back individual messages, especially when a turn has
        multiple tool_use/tool_result cycles.
        """
        if self._turn_start_len is not None:
            del self._messages[self._turn_start_len:]
            self._turn_start_len = None

    def _consume_client_status_events(self) -> list[str]:
        consume = getattr(self._client, "consume_status_events", None)
        if not callable(consume):
            return []
        return list(consume())

    def submit(self, user_input: str | list) -> Iterator[tuple]:
        """Send user message; yield events until the conversation turn completes.

        Yields:
          ("text", str)                         — streamed text chunk
          ("tool_call", name, input)            — before each tool executes
          ("tool_result", name, input, result)  — after each tool executes
          ("waiting",)                          — text done, waiting for tool_use
          ("error", str)                        — non-fatal API error shown to user

        Raises:
          AbortedError — if abort() was called (by Esc listener or Ctrl+C)
        """
        self._aborted = False
        self._turn_start_len = len(self._messages)
        
        new_user_content = _normalize_message_content(user_input)
        if self._messages and self._messages[-1]["role"] == "user":
            prev_content = self._messages[-1]["content"]
            if isinstance(prev_content, list) and isinstance(new_user_content, list):
                self._messages[-1]["content"] = prev_content + new_user_content
            elif isinstance(prev_content, list):
                self._messages[-1]["content"] = prev_content + [{"type": "text", "text": str(user_input)}]
            else:
                self._messages[-1]["content"] = str(prev_content) + "\n\n" + str(user_input)
        else:
            self._messages.append({
                "role": "user",
                "content": new_user_content,
            })
        self._persist(self._messages[-1])

        no_tool_retries = 0
        reasoning_length_empty_recovered = False

        try:
            while True:
                if self._aborted:
                    _logger.info("submit: agent loop aborted by user (Esc / Ctrl+C)")
                    raise AbortedError()

                tool_uses = []

                # API call with retry
                final = None
                for attempt in range(_MAX_RETRIES):
                    try:
                        _api_t0 = time.monotonic()
                        if self._stream:
                            with self._client.stream_messages(
                                model=self._model,
                                max_tokens=self._max_tokens,
                                system=self._system_prompt,
                                tools=[t.to_api_schema() for t in self._tools.values()],
                                messages=self._messages,
                                effort=self._effort,
                            ) as stream:
                                self._active_stream = stream
                                got_text = False
                                for text in stream.text_stream:
                                    if self._aborted:
                                        raise AbortedError()
                                    got_text = True
                                    yield ("text", text)

                                if self._aborted:
                                    raise AbortedError()

                                if got_text:
                                    yield ("waiting",)

                                final = stream.get_final_message()
                        else:
                            final = self._client.create_message(
                                model=self._model,
                                max_tokens=self._max_tokens,
                                system=self._system_prompt,
                                tools=[t.to_api_schema() for t in self._tools.values()],
                                messages=self._messages,
                                effort=self._effort,
                            )
                            for status_message in self._consume_client_status_events():
                                yield ("error", status_message)
                            for block in final.content:
                                if _block_type(block) == "text":
                                    text = str(block.get("text", "") if isinstance(block, dict) else getattr(block, "text", ""))
                                    if text:
                                        yield ("text", text)
                            if any(_block_type(block) == "text" for block in final.content):
                                yield ("waiting",)

                        _api_elapsed = time.monotonic() - _api_t0
                        if final.usage and self._cost_tracker:
                            usage_model = getattr(final, "model", None) or self._model
                            self._cost_tracker.add_usage(usage_model, {
                                "input_tokens": getattr(final.usage, "input_tokens", 0) or 0,
                                "output_tokens": getattr(final.usage, "output_tokens", 0) or 0,
                                "cache_read_input_tokens": getattr(final.usage, "cache_read_input_tokens", 0) or 0,
                                "cache_creation_input_tokens": getattr(final.usage, "cache_creation_input_tokens", 0) or 0,
                            }, api_duration_s=_api_elapsed)
                            yield ("usage", final.usage)
                        for block in final.content:
                            if _block_type(block) == "reasoning":
                                reasoning = str(block.get("text", "") if isinstance(block, dict) else getattr(block, "text", ""))
                                if reasoning:
                                    yield ("reasoning", reasoning)
                            if _block_type(block) == "tool_use":
                                tool_uses.append(block)
                        break  # success, exit retry loop
                    except AbortedError:
                        raise
                    except Exception as e:
                        for status_message in self._consume_client_status_events():
                            yield ("error", status_message)
                        error_msg = self._client.error_message(e)
                        lowered_error_msg = error_msg.lower()

                        if self._client.is_authentication_error(e):
                            _logger.info("submit: agent loop exiting — authentication error: %s", error_msg)
                            self._messages.pop()
                            yield ("error", f"Authentication failed: {error_msg}")
                            return

                        if getattr(self._client, "is_reasoning_length_empty_error", lambda _e: False)(e):
                            if not reasoning_length_empty_recovered:
                                reasoning_length_empty_recovered = True
                                recovery_message = (
                                    "System Recovery: 上一次响应只输出了 reasoning，"
                                    "没有 tool call 或最终内容。请直接输出一个工具调用，"
                                    "不要继续展开推理。"
                                )
                                self._messages.append({
                                    "role": "user",
                                    "content": _normalize_message_content(recovery_message),
                                })
                                self._persist(self._messages[-1])
                                yield ("error", f"API reasoning_length_empty; added recovery signal and retrying once. ({error_msg})")
                                continue
                            if attempt < _MAX_RETRIES - 1:
                                wait = _RETRY_BACKOFF[attempt]
                                yield ("error", f"API reasoning_length_empty, retrying in {wait}s... ({error_msg})")
                                time.sleep(wait)
                            else:
                                _logger.info("submit: agent loop exiting — reasoning_length_empty exhausted all retries")
                                yield ("error", f"API reasoning_length_empty after {_MAX_RETRIES} retries: {error_msg}")
                                return
                            continue

                        # Some OpenAI-compatible upstreams occasionally return
                        # transient empty outputs (especially in streaming tool loops).
                        # Treat these as retryable within the same retry budget.
                        if "upstream model returned empty output" in lowered_error_msg:
                            if attempt < _MAX_RETRIES - 1:
                                wait = _RETRY_BACKOFF[attempt]
                                yield ("error", f"API empty output, retrying in {wait}s... ({error_msg})")
                                time.sleep(wait)
                            else:
                                _logger.info("submit: agent loop exiting — API empty output exhausted all retries")
                                self._messages.pop()
                                yield ("error", f"API error after {_MAX_RETRIES} retries: {error_msg}")
                                return
                            continue

                        if self._client.is_retryable_error(e):
                            if attempt < _MAX_RETRIES - 1:
                                wait = _RETRY_BACKOFF[attempt]
                                yield ("error", f"API error, retrying in {wait}s... ({error_msg})")
                                time.sleep(wait)
                            else:
                                _logger.info("submit: agent loop exiting — retryable API error exhausted all retries: %s", error_msg)
                                self._messages.pop()
                                yield ("error", f"API error after {_MAX_RETRIES} retries: {error_msg}")
                                return
                            continue
                        if self._client.is_api_error(e):
                            _logger.info("submit: agent loop exiting — non-retryable API error: %s", error_msg)
                            self._messages.pop()
                            yield ("error", f"API error: {error_msg}")
                            return
                        if self._aborted:
                            raise AbortedError()
                        _logger.info("submit: agent loop exiting — unhandled error: %s", error_msg)
                        raise
                    finally:
                        self._active_stream = None

                if final is None:
                    _logger.info("submit: agent loop exiting — final is None (API exhausted retries)")
                    self._messages.pop()
                    return

                self._messages.append({
                    "role": "assistant",
                    "content": _normalize_message_content(final.content),
                })
                self._persist(self._messages[-1])

                if not tool_uses:
                    if "finish" in self._tools and no_tool_retries < _MAX_RETRIES:
                        no_tool_retries += 1
                        wait = _RETRY_BACKOFF[no_tool_retries - 1]
                        yield ("error", f"No tools called. Retrying in {wait}s ({no_tool_retries}/{_MAX_RETRIES})...")
                        time.sleep(wait)
                        # 移除 LLM 的无效回复，避免污染上下文
                        self._messages.pop()
                        self._messages.append({
                            "role": "user",
                            "content": _normalize_message_content(
                                "System Error: 你必须且只能输出工具调用 (Tool Call)。如果你已经完成任务，请调用 finish 工具。请勿输出任何纯文本解释。"
                            ),
                        })
                        self._persist(self._messages[-1])
                        continue
                    if "finish" in self._tools and getattr(self._client, "has_fallback", False):
                        self._messages.pop()
                        yield ("error", "[CC-MINI-FALLBACK] no tools called retries exhausted; trying fallback once...")
                        try:
                            _api_t0 = time.monotonic()
                            final = self._client.create_message(
                                model=self._model,
                                max_tokens=self._max_tokens,
                                system=self._system_prompt,
                                tools=[t.to_api_schema() for t in self._tools.values()],
                                messages=self._messages,
                                effort=self._effort,
                                fallback_only=True,
                                fallback_reason="No tools called after retries exhausted",
                            )
                            for status_message in self._consume_client_status_events():
                                yield ("error", status_message)
                            for block in final.content:
                                if _block_type(block) == "text":
                                    text = str(block.get("text", "") if isinstance(block, dict) else getattr(block, "text", ""))
                                    if text:
                                        yield ("text", text)
                            if any(_block_type(block) == "text" for block in final.content):
                                yield ("waiting",)
                            _api_elapsed = time.monotonic() - _api_t0
                            if final.usage and self._cost_tracker:
                                usage_model = getattr(final, "model", None) or self._model
                                self._cost_tracker.add_usage(usage_model, {
                                    "input_tokens": getattr(final.usage, "input_tokens", 0) or 0,
                                    "output_tokens": getattr(final.usage, "output_tokens", 0) or 0,
                                    "cache_read_input_tokens": getattr(final.usage, "cache_read_input_tokens", 0) or 0,
                                    "cache_creation_input_tokens": getattr(final.usage, "cache_creation_input_tokens", 0) or 0,
                                }, api_duration_s=_api_elapsed)
                                yield ("usage", final.usage)
                            tool_uses = [
                                block for block in final.content
                                if _block_type(block) == "tool_use"
                            ]
                            self._messages.append({
                                "role": "assistant",
                                "content": _normalize_message_content(final.content),
                            })
                            self._persist(self._messages[-1])
                            if tool_uses:
                                no_tool_retries = 0
                            else:
                                _logger.info("submit: fallback returned no tool_uses after primary no-tool retries")
                        except Exception as exc:
                            for status_message in self._consume_client_status_events():
                                yield ("error", status_message)
                            yield ("error", f"[CC-MINI-FALLBACK] fallback failed after no-tool retries: {self._client.error_message(exc)}")
                            tool_uses = []
                        finally:
                            self._active_stream = None
                        if not tool_uses:
                            break
                    if not tool_uses:
                        if "finish" in self._tools:
                            _logger.info("submit: agent loop exiting — no tool_uses, finish tool available but no-tool retries exhausted (%d/%d)",
                                         no_tool_retries, _MAX_RETRIES)
                        else:
                            _logger.info("submit: agent loop exiting — no tool_uses, finish tool not registered")
                        break

                no_tool_retries = 0
                reasoning_length_empty_recovered = False
                tool_results = []
                is_finish = False
                for tool_use in tool_uses:
                    if self._aborted:
                        raise AbortedError()
                    if _block_name(tool_use) == "finish":
                        is_finish = True
                        final_answer = _block_input(tool_use).get("final_answer", "")
                        if final_answer:
                            yield ("text", final_answer + "\n")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": _block_id(tool_use),
                            "content": f"Task finished with answer: {final_answer}",
                            "is_error": False,
                        })
                        continue
                    yield ("tool_call", _block_name(tool_use), _block_input(tool_use))
                    result = self._execute_tool(tool_use)
                    yield ("tool_result", _block_name(tool_use), _block_input(tool_use), result)
                    truncated_content = _truncate_tool_result_text(result.content)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": _block_id(tool_use),
                        "content": truncated_content,
                        "is_error": result.is_error,
                    })
                self._messages.append({
                    "role": "user",
                    "content": _normalize_message_content(tool_results),
                })
                self._persist(self._messages[-1])
                if is_finish:
                    break
        except AbortedError:
            self.cancel_turn()
            raise

    def _execute_tool(self, tool_use) -> ToolResult:
        tool_name = _block_name(tool_use)
        tool_input = _block_input(tool_use)
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(content=f"Unknown tool: {tool_name}", is_error=True)

        if self._permissions.check(tool, tool_input) == "deny":
            return ToolResult(content="Permission denied.", is_error=True)

        try:
            # Snapshot file for diff if it's a write tool we want to track
            old_lines: list[str] | None = None
            if self._cost_tracker and tool_name in ("Edit", "Write"):
                fp = tool_input.get("file_path", "")
                try:
                    from pathlib import Path
                    p = Path(fp)
                    old_lines = p.read_text().splitlines() if p.exists() else []
                except Exception:
                    old_lines = None

            result = tool.execute(**tool_input)

            # Track line changes for Edit/Write
            if self._cost_tracker and old_lines is not None and not result.is_error:
                fp = tool_input.get("file_path", "")
                try:
                    from pathlib import Path
                    new_lines = Path(fp).read_text().splitlines()
                    added = max(len(new_lines) - len(old_lines), 0)
                    removed = max(len(old_lines) - len(new_lines), 0)
                    self._cost_tracker.add_lines_changed(added, removed)
                except Exception:
                    pass

            return result
        except Exception as e:
            return ToolResult(content=f"Tool error: {e}", is_error=True)


def _block_type(block: Any) -> str | None:
    if isinstance(block, dict):
        return block.get("type")
    return getattr(block, "type", None)


def _block_name(block: Any) -> str:
    if isinstance(block, dict):
        return str(block.get("name", ""))
    return str(getattr(block, "name", ""))


def _block_id(block: Any) -> str:
    if isinstance(block, dict):
        return str(block.get("id", ""))
    return str(getattr(block, "id", ""))


def _block_input(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        value = block.get("input", {})
    else:
        value = getattr(block, "input", {})
    return value if isinstance(value, dict) else {}
