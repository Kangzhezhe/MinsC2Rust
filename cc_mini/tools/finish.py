"""Finish tool — lets the model signal that it has finished its task and provide a final answer."""

from __future__ import annotations

from .base import Tool, ToolResult

class FinishTool(Tool):
    @property
    def name(self) -> str:
        return "finish"

    @property
    def description(self) -> str:
        return "Call this tool when you have completed all tasks and are ready to provide the final answer to the user."

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "final_answer": {
                    "type": "string",
                    "description": "The final answer or result to present to the user.",
                }
            },
            "required": ["final_answer"],
        }

    def execute(self, **kwargs) -> ToolResult:
        # In practice, the engine will intercept this tool and break out of the loop,
        # but we implement execute to fulfill the Tool interface and provide a fallback.
        final_answer = kwargs.get("final_answer", "")
        return ToolResult(content=f"Task finished with answer: {final_answer}")
