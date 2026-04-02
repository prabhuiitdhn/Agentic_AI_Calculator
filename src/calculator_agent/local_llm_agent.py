from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .tools import InvalidOperationError, Tool, get_tool_registry


class LocalLLMNotAvailableError(RuntimeError):
    """Raised when local LLM tool-calling mode is unavailable."""


@dataclass(frozen=True)
class ToolCallDecision:
    operation: str
    value_a: float
    value_b: float


class LocalLLMCalculatorAgent:
    """Uses a local Ollama model to choose calculator tool and arguments."""

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
        tool_names = ", ".join(sorted(self.tool_registry.keys()))
        system_prompt = (
            "You are a strict calculator tool router. "
            "Return ONLY valid JSON with keys: operation, a, b. "
            f"operation must be one of: {tool_names}. "
            "a and b must be numbers."
        )

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
                },
                "required": ["operation", "a", "b"],
            },
        }

        raw_response = self._post_json(f"{self._base_url}/api/chat", payload)
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
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvalidOperationError(
                "Local model did not return valid tool JSON with operation, a, b."
            ) from exc

    def run(self, prompt: str) -> float:
        decision = self.route(prompt)
        tool = self.tool_registry[decision.operation]
        return tool.execute(decision.value_a, decision.value_b)

    def _ensure_ollama_reachable(self) -> None:
        try:
            request = Request(f"{self._base_url}/api/tags", method="GET")
            with urlopen(request, timeout=12) as response:
                response.read()
        except LocalLLMNotAvailableError:
            raise
        except Exception as exc:  # pragma: no cover
            raise LocalLLMNotAvailableError(
                "Could not connect to local Ollama service. Start Ollama and pull a model."
            ) from exc

    def _post_json(self, url: str, payload: Dict[str, Any]) -> str:
        try:
            body = json.dumps(payload).encode("utf-8")
            request = Request(url, data=body, method="POST")
            request.add_header("Content-Type", "application/json")
            with urlopen(request, timeout=12) as response:
                return response.read().decode("utf-8")
        except URLError as exc:
            raise LocalLLMNotAvailableError(str(exc)) from exc
