# Agentic AI Calculator

This project is a learning-focused agentic calculator built from scratch.

The app runs in local LLM routing mode:
- Local LLM tool calling mode: each operation is exposed as a tool, and a local model chooses tool and arguments from the prompt.

## Features

- Tool-based architecture
- Prompt-to-tool routing
- Local LLM tool calling support (Ollama)
- Deterministic preprocessor for common math word-problem patterns
- Validator and retry pass for suspicious LLM routing results
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

- main.py: CLI entry point for local model routing
- src/calculator_agent/tools.py: tool implementations and registry
- src/calculator_agent/math_preprocessor.py: rule-first parser for common math patterns
- src/calculator_agent/local_llm_agent.py: local tool-calling router
- scripts/benchmark_local_llm.py: small benchmark runner for prompt accuracy checks
- branch_update_agent.py: GitHub push/pull helper

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Prepare local model:

```bash
ollama pull qwen2.5:3b
```

3. Run:

```bash
python main.py
```

If local model service is unavailable, the app shows setup instructions and exits.

## Accuracy Strategy

- Deterministic rules handle common patterns such as rate-over-time, remaining items, and speed-time.
- Local LLM handles general prompt-to-tool routing.
- A retry pass corrects suspicious first-pass decisions for common word-problem mistakes.

## Benchmark

Run the benchmark script to check prompt accuracy quickly:

```bash
python scripts/benchmark_local_llm.py
```

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
