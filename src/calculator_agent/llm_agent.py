from __future__ import annotations

import os
from typing import Any, Dict

from .tools import CalculatorError, InvalidOperationError, get_tool_registry


class LLMNotAvailableError(Exception):
    pass


# Claude tool definitions — one tool per calculator operation.
# Claude reads these and decides which one to call + with what arguments.
_CLAUDE_TOOLS: list[Dict[str, Any]] = [
    {
        "name": "add",
        "description": "Adds two numbers together.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "subtract",
        "description": "Subtracts the second number from the first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Number to subtract from"},
                "b": {"type": "number", "description": "Number to subtract"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "multiply",
        "description": "Multiplies two numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "divide",
        "description": "Divides the first number by the second.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Dividend"},
                "b": {"type": "number", "description": "Divisor (must not be zero)"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "power",
        "description": "Raises the first number to the power of the second.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Base"},
                "b": {"type": "number", "description": "Exponent"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "modulus",
        "description": "Returns the remainder after dividing the first number by the second.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "Dividend"},
                "b": {"type": "number", "description": "Divisor (must not be zero)"},
            },
            "required": ["a", "b"],
        },
    },
]

_SYSTEM_PROMPT = (
    "You are a calculator agent. "
    "The user will give you a mathematical expression or question in natural language. "
    "You must always respond by calling exactly one of the provided tools with the correct numbers. "
    "Never answer in plain text — always use a tool call."
)


class LLMCalculatorAgent:
    """
    Uses Claude's tool-use feature to parse any natural language math prompt
    and route it to the correct calculator tool.

    Agentic pattern:
      1. User sends a prompt.
      2. Claude reads tools + prompt and responds with a tool_use block
         (operation name + arguments a, b).
      3. We execute the chosen tool locally with those arguments.
      4. Result is returned to the user.

    Falls back gracefully: instantiation raises LLMNotAvailableError when
    the anthropic package or ANTHROPIC_API_KEY is missing, so callers can
    fall back to the regex agent.
    """

    MODEL = "claude-3-5-haiku-20241022"

    def __init__(self) -> None:
        try:
            import anthropic  # noqa: PLC0415  (lazy import — only when actually used)
        except ImportError as exc:
            raise LLMNotAvailableError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise LLMNotAvailableError(
                "ANTHROPIC_API_KEY environment variable not set."
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        self._tool_registry = get_tool_registry()

    def run(self, prompt: str) -> float:
        """Parse prompt via Claude tool-use and execute the selected tool."""
        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=256,
            system=_SYSTEM_PROMPT,
            tools=_CLAUDE_TOOLS,
            messages=[{"role": "user", "content": prompt}],
        )

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )

        if tool_use_block is None:
            raise InvalidOperationError(
                f"Claude did not select a tool for: '{prompt}'. "
                "Try rephrasing your math expression."
            )

        operation = tool_use_block.name
        args: Dict[str, Any] = tool_use_block.input

        if operation not in self._tool_registry:
            raise InvalidOperationError(f"Claude selected unknown operation: {operation}")

        try:
            a = float(args["a"])
            b = float(args["b"])
        except (KeyError, ValueError, TypeError) as exc:
            raise CalculatorError(
                f"Claude returned invalid arguments for {operation}: {args}"
            ) from exc

        tool = self._tool_registry[operation]
        return tool.execute(a, b)

    @property
    def mode_label(self) -> str:
        return f"Claude ({self.MODEL})"
