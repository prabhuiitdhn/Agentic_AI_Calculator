from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable

from .agent import CalculatorAgent
from .tools import InvalidOperationError, Tool, get_tool_registry

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover
    Anthropic = None


class LLMNotAvailableError(RuntimeError):
    """Raised when tool-calling LLM cannot be used."""


@dataclass(frozen=True)
class ToolCallDecision:
    operation: str
    value_a: float
    value_b: float


class LLMCalculatorAgent(CalculatorAgent):
    """Uses Claude tool calling to map prompt to calculator tool invocation."""

    def __init__(self, tool_registry: Dict[str, Tool] | None = None) -> None:
        super().__init__(tool_registry=tool_registry or get_tool_registry())
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if Anthropic is None:
            raise LLMNotAvailableError("anthropic package is not installed.")
        if not api_key:
            raise LLMNotAvailableError("ANTHROPIC_API_KEY is not set.")

        self._client = Anthropic(api_key=api_key)
        self._model = "claude-3-5-haiku-20241022"
        self._tool_schemas = self._build_tool_schemas()

    def list_tools(self) -> Iterable[Tool]:
        return self.tool_registry.values()

    def route(self, prompt: str) -> ToolCallDecision:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=300,
            temperature=0,
            system=(
                "You are a calculator router. Always use exactly one provided tool. "
                "Choose the best operation from user intent and extract two numeric inputs a and b."
            ),
            tools=self._tool_schemas,
            messages=[{"role": "user", "content": prompt}],
        )

        tool_block = None
        for block in response.content:
            if getattr(block, "type", "") == "tool_use":
                tool_block = block
                break

        if tool_block is None:
            raise InvalidOperationError("Model did not return a tool call.")

        operation = tool_block.name
        if operation not in self.tool_registry:
            raise InvalidOperationError(f"Unsupported operation selected by model: {operation}")

        input_data: Dict[str, Any] = dict(tool_block.input or {})
        if "a" not in input_data or "b" not in input_data:
            raise ValueError("Tool call must contain both 'a' and 'b'.")

        return ToolCallDecision(
            operation=operation,
            value_a=float(input_data["a"]),
            value_b=float(input_data["b"]),
        )

    def run(self, prompt: str) -> float:
        decision = self.route(prompt)
        tool = self.tool_registry[decision.operation]
        return tool.execute(decision.value_a, decision.value_b)

    def _build_tool_schemas(self) -> list[dict[str, Any]]:
        schemas: list[dict[str, Any]] = []
        for operation_name, tool in self.tool_registry.items():
            schemas.append(
                {
                    "name": operation_name,
                    "description": tool.description,
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First numeric value."},
                            "b": {"type": "number", "description": "Second numeric value."},
                        },
                        "required": ["a", "b"],
                    },
                }
            )
        return schemas