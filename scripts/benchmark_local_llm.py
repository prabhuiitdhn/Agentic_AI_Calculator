from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from calculator_agent.local_llm_agent import LocalLLMCalculatorAgent


def main() -> int:
    prompts = [
        ("add 4 and 7", 11.0),
        ("what is 15 minus 4", 11.0),
        ("multiply 6 and 8", 48.0),
        (
            "choose the number of balls in the packets - 1 balls is being added on every 5 minutes and after one hours how many balls will be there?",
            12.0,
        ),
        ("If a man hold 10 eggs and 5 eggs got crashed then how many eggs remain", 5.0),
        ("A car moves at 40 km/h for 3 hours. How far does it travel?", 120.0),
    ]
    agent = LocalLLMCalculatorAgent()
    failures = 0

    for prompt, expected in prompts:
        actual = agent.run(prompt)
        passed = abs(actual - expected) < 1e-9
        status = "PASS" if passed else "FAIL"
        print(f"{status} | expected={expected} | actual={actual} | prompt={prompt}")
        if not passed:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())