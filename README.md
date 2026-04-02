# Agentic AI Calculator (From Scratch)

This project is a learning-focused **agentic calculator** built from scratch.

The idea:
- You type a natural language command prompt.
- The agent extracts the operation and numbers.
- The agent routes the request to a specific tool function.
- The selected tool executes and returns the result.

## Features

- Tool-based architecture
- Prompt-to-tool routing
- Operations implemented from scratch:
  - add
  - subtract
  - multiply
  - divide
  - power
  - modulus
- Interactive CLI loop

## Project Structure

- `main.py` - CLI entry point
- `src/calculator_agent/agent.py` - prompt parsing and tool routing
- `src/calculator_agent/tools.py` - tool functions and registry

## Setup

1. Use your existing Python interpreter.
2. From project root, run:

```bash
python main.py
```

No external packages are required for this starter project.

## Commands

- `help` or `tools` - show available tools
- `guided` - ask operation and two inputs explicitly
- `exit` or `quit` - close the calculator

## Prompt Style

You can use both natural language and operator symbols.

- Natural language: `what is 15 minus 4`
- Symbol style: `15 - 4`

## Start the app

```bash
python main.py
```

## GitHub Branch Update Agent

You can also run a separate agent that asks for a GitHub repository and applies the same code update branch-wise.

Run:

```bash
python branch_update_agent.py
```

Flow:

1. Enter the GitHub repo URL.
2. Select one or more remote branches (or all).
3. Provide a file path in that repo.
4. Provide find/replace text.
5. Provide commit message.
6. Optionally push each updated branch.

Notes:

- It clones the repository into `./repos` (or fetches if already present).
- It checks out each selected branch, pulls latest, applies the replacement, commits, and optionally pushes.
- Git auth must already work on your machine for clone/pull/push.

## Example Prompts

- `add 5 and 9`
- `what is 15 minus 4`
- `multiply 3.5 and 2`
- `divide 100 by 8`
- `raise 2 to 10`
- `modulus 10 and 3`
- `4 + 7`
- `12 % 5`

## Next Learning Upgrades

- Add memory/state so the agent can reference last result.
- Add validation layer and richer error recovery.
- Add planner-executor style routing (multi-step tasks).
- Add unit tests for parser and tools.
