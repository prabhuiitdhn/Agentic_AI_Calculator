from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .tools import InvalidOperationError, Tool, get_tool_registry


@dataclass(frozen=True)
class AgentDecision:
    """Result of routing a prompt to a calculator tool."""

    operation: str
    value_a: float
    value_b: float


class CalculatorAgent:
    """Simple keyword-based router from text prompt to tool execution."""

    def __init__(self, tool_registry: Dict[str, Tool] | None = None) -> None:
        self.tool_registry = tool_registry or get_tool_registry()
        self.alias_map = self._build_alias_map()
        self.symbol_map = self._build_symbol_map()

    def _build_alias_map(self) -> Dict[str, str]:
        """Maps human-friendly aliases to canonical tool names."""

        return {
            "add": "add",
            "plus": "add",
            "sum": "add",
            "subtract": "subtract",
            "minus": "subtract",
            "difference": "subtract",
            "multiply": "multiply",
            "times": "multiply",
            "product": "multiply",
            "divide": "divide",
            "divided": "divide",
            "quotient": "divide",
            "power": "power",
            "exponent": "power",
            "raise": "power",
            "mod": "modulus",
            "modulus": "modulus",
            "remainder": "modulus",
        }

    def _build_symbol_map(self) -> Dict[str, str]:
        """Maps operator symbols to canonical tool names."""

        return {
            "+": "add",
            "-": "subtract",
            "*": "multiply",
            "x": "multiply",
            "/": "divide",
            "^": "power",
            "%": "modulus",
        }

    def list_tools(self) -> Iterable[Tool]:
        return self.tool_registry.values()

    def route(self, prompt: str) -> AgentDecision:
        """Extracts operation and two numbers from a free-form prompt."""

        operation = self.resolve_operation(prompt)
        value_a, value_b = self._extract_two_numbers(prompt)
        return AgentDecision(operation=operation, value_a=value_a, value_b=value_b)

    def resolve_operation(self, text: str) -> str:
        """Returns the canonical operation name from prompt text."""

        return self._extract_operation(text)

    def run(self, prompt: str) -> float:
        decision = self.route(prompt)
        tool = self.tool_registry[decision.operation]
        return tool.execute(decision.value_a, decision.value_b)

    def _extract_operation(self, prompt: str) -> str:
        symbol_tokens = re.findall(r"[+\-*/^%x]", prompt.lower())
        for token in symbol_tokens:
            if token in self.symbol_map:
                operation = self.symbol_map[token]
                if operation in self.tool_registry:
                    return operation

        tokens = re.findall(r"[a-zA-Z]+", prompt.lower())
        for token in tokens:
            if token in self.alias_map:
                operation = self.alias_map[token]
                if operation in self.tool_registry:
                    return operation
        available = ", ".join(sorted(self.tool_registry.keys()))
        raise InvalidOperationError(
            f"Could not detect a valid operation in the prompt. Available: {available}"
        )

    def _extract_two_numbers(self, prompt: str) -> Tuple[float, float]:
        numbers = re.findall(r"[-+]?\d*\.?\d+", prompt)
        if len(numbers) < 2:
            raise ValueError("Please provide at least two numbers in the prompt.")
        return float(numbers[0]), float(numbers[1])
