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

You can also run a simplified GitHub helper agent for day-to-day development sync.

Run:

```bash
python branch_update_agent.py
```

Flow:

1. Enter the GitHub repo URL.
2. Enter your local development repo path (default is current project path).
3. Choose mode:
  - `1. Push current code to main`
  - `2. Push current code to another branch`
  - `3. Pull latest code to local repo`

Main branch mode:

1. Switches to `main` (creates it if needed).
2. Pulls latest from origin.
3. Commits local changes and pushes to `main`.
4. Pulls again to keep local up to date.

Any other branch mode:

1. Enter branch name.
2. If branch exists, it checks out and pulls latest.
3. If branch does not exist, it creates branch from `main` (or orphan fallback).
4. Commits local changes, pushes branch, then pulls latest.

Pull latest code mode:

1. Enter branch name (default is current branch).
2. Agent checks out the branch and pulls latest from origin.

Notes:

- If the provided local path is not a git repo, the agent uses/creates a cached clone in `./repos`.
- The agent updates `origin` URL to the repository you provide.
- Git auth must already work on your machine for clone/pull/push.

## Project Session Agent (Secure API Key Scope)

Use this script to load `ANTHROPIC_API_KEY` only for the current project session.
When the session exits, the key is removed from that process.

1. Create `.env` in project root:

```bash
ANTHROPIC_API_KEY=your_real_key_here
```

2. Start a session (uses Marigold Python automatically if available):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/project_session_agent.ps1
```

3. Optional explicit Marigold command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/project_session_agent.ps1 -StartupCommand "& 'C:/Users/uib43225/AppData/Local/anaconda3/envs/Marigold/python.exe' main.py"
```

4. Exit session by typing `exit` at `project-shell>` prompt.

Notes:

- `.env` is ignored by git, so the key is not pushed to GitHub.
- If `.env` is missing, the session script exits with a clear error.

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
