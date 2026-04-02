from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .math_preprocessor import MathPlan, preprocess_prompt
from .tools import InvalidOperationError, Tool, get_tool_registry


class LocalLLMNotAvailableError(RuntimeError):
    """Raised when local LLM tool-calling mode is unavailable."""


@dataclass(frozen=True)
class ToolCallDecision:
    operation: str
    value_a: float
    value_b: float
    strategy: str = "llm"


class LocalLLMCalculatorAgent:
    """Uses a local Ollama model for tool routing with rule-based prechecks."""

    def __init__(self, tool_registry: Dict[str, Tool] | None = None) -> None:
        self.tool_registry = tool_registry or get_tool_registry()
        self._base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self._model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()
        if not self._model:
            raise LocalLLMNotAvailableError("OLLAMA_MODEL is empty.")
        self._ensure_ollama_reachable()

    def list_tools(self) -> Iterable[Tool]:
        return self.tool_registry.values()

    def route(self, prompt: str) -> ToolCallDecision:
        deterministic_plan = preprocess_prompt(prompt)
        if deterministic_plan is not None:
            return self._decision_from_plan(deterministic_plan)

        tool_call = self._request_tool_call(prompt)
        if self._needs_retry(prompt, tool_call):
            tool_call = self._request_tool_call(prompt, correction_hint=self._retry_hint(prompt))
        return tool_call

    def run(self, prompt: str) -> float:
        decision = self.route(prompt)
        tool = self.tool_registry[decision.operation]
        return tool.execute(decision.value_a, decision.value_b)

    def _request_tool_call(self, prompt: str, correction_hint: str = "") -> ToolCallDecision:
        tool_names = ", ".join(sorted(self.tool_registry.keys()))
        system_prompt = (
            "You are a strict calculator planner. Return ONLY valid JSON with keys "
            "operation, a, b, reasoning_type, confidence. "
            f"operation must be one of: {tool_names}. "
            "a and b must be numbers. reasoning_type must describe the math pattern briefly. "
            "confidence must be a number from 0 to 1. Use the mathematically correct transformation for word problems."
        )
        if correction_hint:
            system_prompt = f"{system_prompt} {correction_hint}"

        payload = {
            "model": self._model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "format": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": sorted(self.tool_registry.keys()),
                    },
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "reasoning_type": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["operation", "a", "b", "reasoning_type", "confidence"],
            },
        }

        raw_response = self._post_json(f"{self._base_url}/api/chat", payload)
        return self._parse_tool_call(raw_response)

    def _parse_tool_call(self, raw_response: str) -> ToolCallDecision:
        try:
            parsed = json.loads(raw_response)
            content = parsed["message"]["content"]
            tool_call = json.loads(content)
            operation = str(tool_call["operation"])
            if operation not in self.tool_registry:
                raise InvalidOperationError(
                    f"Unsupported operation selected by local model: {operation}"
                )
            return ToolCallDecision(
                operation=operation,
                value_a=float(tool_call["a"]),
                value_b=float(tool_call["b"]),
                strategy=str(tool_call.get("reasoning_type", "llm")),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidOperationError(
                "Local model did not return valid tool JSON with operation, a, and b."
            ) from exc

    def _needs_retry(self, prompt: str, decision: ToolCallDecision) -> bool:
        text = prompt.lower()
        if any(token in text for token in ("every", "per hour", "each hour")) and decision.operation == "add":
            return True
        if any(token in text for token in ("remain", "remaining", "left", "lost", "broken", "crashed")) and decision.operation != "subtract":
            return True
        return False

    def _retry_hint(self, prompt: str) -> str:
        text = prompt.lower()
        if "every" in text:
            return "For rate problems, convert total duration into intervals and prefer multiplication or division over direct addition."
        if any(token in text for token in ("remain", "remaining", "left", "lost", "broken", "crashed")):
            return "For remaining-item problems, prefer subtraction using starting quantity minus removed quantity."
        return "Re-evaluate the word problem carefully before selecting the operation."

    def _decision_from_plan(self, plan: MathPlan) -> ToolCallDecision:
        return ToolCallDecision(
            operation=plan.operation,
            value_a=plan.a,
            value_b=plan.b,
            strategy=plan.strategy,
        )

    def _ensure_ollama_reachable(self) -> None:
        try:
            request = Request(f"{self._base_url}/api/tags", method="GET")
            with urlopen(request, timeout=12) as response:
                response.read()
        except Exception as exc:  # pragma: no cover
            raise LocalLLMNotAvailableError(
                "Could not connect to local Ollama service. Start Ollama and pull a model."
            ) from exc

    def _post_json(self, url: str, payload: Dict[str, Any]) -> str:
        try:
            body = json.dumps(payload).encode("utf-8")
            request = Request(url, data=body, method="POST")
            request.add_header("Content-Type", "application/json")
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8")
        except URLError as exc:
            raise LocalLLMNotAvailableError(str(exc)) from exc