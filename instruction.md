# Beginner Guide: Run This Project with Ollama (Local LLM)

This guide explains how to set up everything from scratch and run the calculator project end to end.

## 1. Prerequisites

- Windows machine
- Python installed (you already have Conda/Python in this project)
- Internet connection (to download Ollama model)

## 2. Open Project Folder

Open PowerShell in the project root:

```powershell
cd D:\innovation\agentic_ai_scratch
```

## 3. Install Ollama

Install using winget:

```powershell
winget install Ollama.Ollama
```

If installation is already done, this step can be skipped.

## 4. Verify Ollama Installation

```powershell
ollama --version
```

If command is not found:
- Close terminal
- Open a new PowerShell
- Run `ollama --version` again

## 5. Start Ollama Service

Usually Ollama runs automatically after install. If needed:

```powershell
ollama serve
```

If you get this error:

```text
bind: Only one usage of each socket address ...
```

It means Ollama is already running on port `11434`. That is okay. Do not start it again.

## 6. Pull Local Model

Download the model used by this project:

```powershell
ollama pull qwen2.5:3b
```

Verify model is present:

```powershell
ollama list
```

## 7. (Optional) Set Default Model Variable

```powershell
setx OLLAMA_MODEL "qwen2.5:3b"
```

Then open a new terminal for this to take effect.

## 8. Install Python Dependencies

From project root:

```powershell
pip install -r requirements.txt
```

## 9. Run Calculator App

```powershell
python main.py
```

Expected startup output includes:

```text
Parser mode: local-llm-tool-calling
```

This confirms local Ollama mode is active.

## 10. Try Example Prompts

Inside calculator prompt:

- `add 4 and 7`
- `what is 10 divided by 2`
- `multiply 6 and 8`
- `12 % 5`
- `If a man hold 10 eggs and 5 eggs got crashed then how many eggs remain`

Type `exit` to quit.

## 11. Common Issues and Fixes

### Issue A: `Local model setup error`

Fix:
1. Confirm Ollama is installed: `ollama --version`
2. Confirm model exists: `ollama list`
3. Pull model again: `ollama pull qwen2.5:3b`
4. Re-run: `python main.py`

### Issue B: `ollama serve` port bind error

Cause:
- Ollama already running.

Fix:
- Do not run `ollama serve` again.
- Use `ollama list` or `ollama run ...` directly.

### Issue C: `ollama` command not recognized

Fix:
1. Restart terminal/VS Code
2. Reinstall with `winget install Ollama.Ollama`
3. Check path with:

```powershell
where.exe ollama
```

## 12. Run Git Helper (Optional)

If you want to push/pull code using helper script:

```powershell
python branch_update_agent.py
```

Use mode:
- `1` push to main
- `2` push to another branch
- `3` pull latest code

## 13. Quick End-to-End Checklist

- [ ] `ollama --version` works
- [ ] `ollama list` shows `qwen2.5:3b`
- [ ] `python main.py` starts
- [ ] Parser mode shows `local-llm-tool-calling`
- [ ] Sample prompt returns result
