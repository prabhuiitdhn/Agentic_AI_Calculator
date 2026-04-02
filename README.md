# Agentic AI Calculator

This project is a learning-focused agentic calculator built from scratch.

The app supports two routing modes:
- Claude tool calling mode (primary): each operation is exposed as a tool, and the model chooses the tool and arguments from the prompt.
- Regex fallback mode: local parser routes prompts to tools when LLM is unavailable.

## Features

- Tool-based architecture
- Prompt-to-tool routing
- Claude tool calling support (Anthropic API)
- Offline/local fallback routing
- Interactive CLI loop
- GitHub helper script for branch push/pull workflows

## Operations (Tools)

- add
- subtract
- multiply
- divide
- power
- modulus

## Project Structure

- main.py: CLI entry point and mode fallback logic
- src/calculator_agent/tools.py: tool implementations and registry
- src/calculator_agent/agent.py: local regex router
- src/calculator_agent/llm_agent.py: Claude tool-calling router
- branch_update_agent.py: GitHub push/pull helper

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your API key (optional but recommended for tool-calling mode):

```bash
set ANTHROPIC_API_KEY=your_key_here
```

3. Run:

```bash
python main.py
```

If API key or Anthropic package is unavailable, the app automatically uses regex fallback.

## Commands

- help or tools: show available tools
- guided: ask operation and two inputs explicitly
- exit or quit: close the calculator

## Prompt Style

Both natural language and operator symbols are supported.

- Natural language: what is 15 minus 4
- Symbol style: 15 - 4

## GitHub Branch Update Agent

Run:

```bash
python branch_update_agent.py
```

Flow:

1. Enter GitHub repo URL.
2. Enter local development repo path (default is current project path).
3. Choose mode:
   - 1. Push current code to main
   - 2. Push current code to another branch
   - 3. Pull latest code to local repo

Notes:

- If the provided local path is not a git repo, the agent uses or creates a cached clone in ./repos.
- The agent updates origin URL to the repository you provide.
- Git auth must already work on your machine for clone, pull, and push.

## Example Prompts

- add 5 and 9
- what is 15 minus 4
- multiply 3.5 and 2
- divide 100 by 8
- raise 2 to 10
- modulus 10 and 3
- 4 + 7
- 12 % 5
- If a man hold 10 eggs and 5 eggs got crashed then how many eggs remain
