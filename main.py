from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from calculator_agent.agent import CalculatorAgent
from calculator_agent.llm_agent import LLMCalculatorAgent, LLMNotAvailableError
from calculator_agent.tools import CalculatorError


def build_agent() -> tuple[object, str]:
    """Try LLM agent first; fall back to regex agent if unavailable."""
    try:
        agent = LLMCalculatorAgent()
        return agent, agent.mode_label
    except LLMNotAvailableError as exc:
        print(f"[LLM unavailable — using regex parser] {exc}")
        agent = CalculatorAgent()
        return agent, "regex"


def print_welcome(agent: object, mode: str) -> None:
    print(f"\nAgentic Calculator  |  intent parser: {mode}\n")
    print("Type any math expression in plain language:")
    print("  what is 20 percent of 150")
    print("  add 4 and 7")
    print("  divide 100 by 8")
    print("  2 to the power of 10")
    print("Commands: help, guided, exit\n")

    tools = (
        agent.tool_registry.values()
        if hasattr(agent, "tool_registry")
        else []
    )
    if tools:
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        print()


def run_guided_mode(agent: object) -> None:
    """Step-by-step mode: ask operation and numbers separately."""
    print("\nGuided mode")
    op_input = input("operation> ").strip()
    try:
        if hasattr(agent, "resolve_operation"):
            operation = agent.resolve_operation(op_input)
        else:
            # LLM agent: parse a one-word prompt to get the operation
            from calculator_agent.agent import CalculatorAgent
            fallback = CalculatorAgent()
            operation = fallback.resolve_operation(op_input)
    except Exception as exc:
        print(f"Error: {exc}\n")
        return

    try:
        a = float(input("first number> ").strip())
        b = float(input("second number> ").strip())
        from calculator_agent.tools import get_tool_registry
        tool = get_tool_registry()[operation]
        print(f"Result: {tool.execute(a, b)}\n")
    except (CalculatorError, ValueError) as exc:
        print(f"Error: {exc}\n")


def run_cli() -> None:
    agent, mode = build_agent()
    print_welcome(agent, mode)

    while True:
        user_input = input("calculator> ").strip()
        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in {"exit", "quit"}:
            print("Goodbye.")
            break
        if lowered in {"help", "tools"}:
            print_welcome(agent, mode)
            continue
        if lowered == "guided":
            run_guided_mode(agent)
            continue

        try:
            result = agent.run(user_input)
            print(f"Result: {result}\n")
        except (CalculatorError, ValueError) as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    run_cli()
