from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from .config import AppConfig, load_app_config
from .context import build_system_prompt
from .cost_tracker import CostTracker
from .engine import Engine
from .compact import CompactService, should_compact
from .shared_logger import configure_ccmini_logger
from .permissions import PermissionChecker
from .sandbox.config import load_sandbox_config
from .sandbox.manager import SandboxManager
from .tools.bash import BashTool
from .tools.file_edit import FileEditTool
from .tools.file_read import FileReadTool
from .tools.file_write import FileWriteTool
from .tools.glob_tool import GlobTool
from .tools.grep_tool import GrepTool
from .tools.rust_debug_script import RustDebugScriptTool
# from .tools.ask_user import AskUserQuestionTool
from .tools.finish import FinishTool


@dataclass(frozen=True)
class CCMiniOptions:
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    max_tokens: int | None = None
    effort: str | None = None
    stream: bool | None = None
    config: str | None = None
    memory_dir: str | None = None
    auto_approve: bool = True
    compact_check_each_tool_result: bool = True
    compact_log_path: str | None = None


class CCMini:
    """Python 调用入口。"""

    def __init__(
        self,
        options: CCMiniOptions | None = None,
        on_tool_call: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, dict, object], None] | None = None,
        on_reasoning: Callable[[str], None] | None = None,
    ):
        self.options = options or CCMiniOptions()
        self.app_config = _load_config(self.options)
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_reasoning = on_reasoning

        configure_ccmini_logger(self.options.compact_log_path)

        sandbox_config = load_sandbox_config(self.app_config.config_paths)
        sandbox_mgr = SandboxManager(config=sandbox_config)

        permissions = PermissionChecker(
            auto_approve=self.options.auto_approve,
            sandbox_manager=sandbox_mgr,
        )

        tools = [
            FileReadTool(),
            GlobTool(),
            GrepTool(),
            FileEditTool(),
            FileWriteTool(),
            BashTool(sandbox_manager=sandbox_mgr),
            #AskUserQuestionTool(),
        ]
        
        use_finish_tool = getattr(self.app_config, "use_finish_tool", False)
        if use_finish_tool:
            tools.append(FinishTool())

        system_prompt = build_system_prompt(
            cwd=str(Path.cwd()),
            memory_dir=self.app_config.memory_dir,
            use_finish_tool=use_finish_tool,
        )

        self.cost_tracker = CostTracker()

        self.engine = Engine(
            tools=tools,
            system_prompt=system_prompt,
            permission_checker=permissions,
            provider=self.app_config.provider,
            api_key=self.app_config.api_key,
            base_url=self.app_config.base_url,
            model=self.app_config.model,
            max_tokens=self.app_config.max_tokens,
            effort=self.app_config.effort,
            openai_extra_body=self.app_config.openai_extra_body,
            thinking=self.app_config.thinking,
            stream=self.app_config.stream,
            fallback=self.app_config.fallback,
            cost_tracker=self.cost_tracker,
        )
        self.compact_service = CompactService(
            client=self.engine._client,
            model=self.app_config.model,
            effort=self.app_config.effort,
        )

    def _maybe_auto_compact(self) -> None:
        if should_compact(
            self.engine.get_messages(),
            model=self.app_config.model,
            last_input_tokens=self.cost_tracker.last_input_tokens,
        ):
            new_msgs, _ = self.compact_service.compact(
                self.engine.get_messages(),
                self.engine.get_system_prompt(),
            )
            self.engine.set_messages(new_msgs)

    def call(self, prompt: str | list) -> str:
        self._maybe_auto_compact()
        chunks: list[str] = []
        for event in self.engine.submit(prompt):
            event_type = event[0]
            if event_type == "text":
                chunks.append(event[1])
            elif event_type == "reasoning":
                if self.on_reasoning is not None:
                    self.on_reasoning(event[1])
            elif event_type == "tool_call":
                _, tool_name, tool_input = event
                if self.on_tool_call is not None:
                    self.on_tool_call(tool_name, tool_input)
            elif event_type == "tool_result":
                _, tool_name, tool_input, result = event
                if self.on_tool_result is not None:
                    self.on_tool_result(tool_name, tool_input, result)
                if self.options.compact_check_each_tool_result:
                    self._maybe_auto_compact()
            elif event_type == "error":
                import sys
                print(f"[Engine Error/Warning] {event[1]}", file=sys.stderr)
        return "".join(chunks)

    def stream(self, prompt: str | list) -> Iterator[str]:
        self._maybe_auto_compact()
        for event in self.engine.submit(prompt):
            event_type = event[0]
            if event_type == "text":
                yield event[1]
            elif event_type == "reasoning":
                if self.on_reasoning is not None:
                    self.on_reasoning(event[1])
            elif event_type == "tool_call":
                _, tool_name, tool_input = event
                if self.on_tool_call is not None:
                    self.on_tool_call(tool_name, tool_input)
            elif event_type == "tool_result":
                _, tool_name, tool_input, result = event
                if self.on_tool_result is not None:
                    self.on_tool_result(tool_name, tool_input, result)
                if self.options.compact_check_each_tool_result:
                    self._maybe_auto_compact()
            elif event_type == "error":
                import sys
                print(f"[Engine Error/Warning] {event[1]}", file=sys.stderr)

    def close(self) -> None:
        close = getattr(getattr(self, "engine", None), "close", None)
        if callable(close):
            close()


def _load_config(options: CCMiniOptions) -> AppConfig:
    args = Namespace(
        prompt=None,
        print=False,
        auto_approve=options.auto_approve,
        config=options.config,
        provider=options.provider,
        api_key=options.api_key,
        base_url=options.base_url,
        model=options.model,
        max_tokens=options.max_tokens,
        effort=options.effort,
        stream=options.stream,
        resume=None,
        memory_dir=options.memory_dir,
        no_auto_dream=False,
        dream_interval=None,
        dream_min_sessions=None,
        coordinator=False,
    )
    return load_app_config(args)


__all__ = ["CCMini", "CCMiniOptions"]
