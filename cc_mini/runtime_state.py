from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRuntimeState:
    iteration: int = 0
    consecutive_tool_calls: int = 0
    force_final_answer: bool = False
    final_answer_notice: str = ""
    tool_format_retry_notice: str = ""
    no_progress_steps: int = 0
    phase: str = "tool"


@dataclass
class RuntimeSnapshot:
    state: AgentRuntimeState
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    latest_response: Any = None
