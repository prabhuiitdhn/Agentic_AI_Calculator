from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from calculator_agent.local_llm_agent import LocalLLMCalculatorAgent, LocalLLMNotAvailableError
from calculator_agent.tools import CalculatorError


def print_welcome(agent: LocalLLMCalculatorAgent, mode: str) -> None:
    print("\nAgentic Calculator (from scratch)\n")
    print(f"Parser mode: {mode}\n")
    print("Type prompts like:")
    print("  add 4 and 7")
    print("  4 + 7")
    print("  what is 10 divided by 2")
    print("  multiply 6 and 8")
    print("Commands: help, tools, guided, exit\n")

    print("Available tools:")
    for tool in agent.list_tools():
        print(f"  - {tool.name}: {tool.description}")
    print()


def build_agent() -> tuple[LocalLLMCalculatorAgent, str]:
    return LocalLLMCalculatorAgent(), "local-llm-tool-calling"


def run_cli() -> None:
    try:
        agent, mode = build_agent()
    except LocalLLMNotAvailableError as exc:
        print(f"Local model setup error: {exc}")
        print("Start Ollama and ensure model exists (example: ollama pull qwen2.5:3b).")
        return

    print_welcome(agent, mode)

    def run_guided_mode() -> None:
        print("\nGuided mode")
        available_ops = sorted(agent.tool_registry.keys())
        print(f"Available operations: {', '.join(available_ops)}")
        operation = input("operation> ").strip().lower()
        if operation not in agent.tool_registry:
            print(f"Error: operation must be one of: {', '.join(available_ops)}\n")
            return

        first_value_raw = input("first number> ").strip()
        second_value_raw = input("second number> ").strip()
        try:
            first_value = float(first_value_raw)
            second_value = float(second_value_raw)
            tool = agent.tool_registry[operation]
            result = tool.execute(first_value, second_value)
            print(f"Result: {result}\n")
        except (CalculatorError, ValueError) as exc:
            print(f"Error: {exc}\n")

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
            run_guided_mode()
            continue

        try:
            result = agent.run(user_input)
            print(f"Result: {result}\n")
        except (CalculatorError, ValueError) as exc:
            print(f"Error: {exc}\n")
        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    run_cli()
