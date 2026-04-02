from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from calculator_agent.agent import CalculatorAgent
from calculator_agent.tools import CalculatorError


def print_welcome(agent: CalculatorAgent) -> None:
    print("\nAgentic Calculator (from scratch)\n")
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


def run_cli() -> None:
    agent = CalculatorAgent()
    print_welcome(agent)

    def run_guided_mode() -> None:
        print("\nGuided mode")
        op_input = input("operation> ").strip()
        try:
            operation = agent.resolve_operation(op_input)
        except Exception as exc:
            print(f"Error: {exc}\n")
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
            print_welcome(agent)
            continue

        if lowered == "guided":
            run_guided_mode()
            continue

        try:
            result = agent.run(user_input)
            print(f"Result: {result}\n")
        except (CalculatorError, ValueError) as exc:
            print(f"Error: {exc}\n")


if __name__ == "__main__":
    run_cli()
