# GitMsg

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Typer](https://img.shields.io/badge/Typer-000000?style=for-the-badge&logo=python&logoColor=white)
![Rich](https://img.shields.io/badge/Rich-000000?style=for-the-badge&logo=python&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black)

---

A local-first Python CLI that analyzes staged Git changes and generates meaningful Conventional Commit messages — no AI or API keys required.

---

## How It Works

```text
Git staged changes
       ↓
Parse staged diff
       ↓
Analyze changed files
       ↓
Classify the change
       ↓
Determine scope
       ↓
Generate Conventional Commit
       ↓
Show confidence + reasoning
       ↓
Copy message to clipboard
```

---

## Features

- **Staged Diff Analysis** — Parses `git diff --cached` to inspect only what's about to be committed
- **File Change Detection** — Identifies added, modified, deleted, renamed, and copied files
- **Automatic Classification** — Determines the Conventional Commit type (`feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `build`, `ci`, `perf`)
- **Scope Inference** — Detects the scope from file paths when consistent enough (e.g., `feat(auth):`, `fix(api):`)
- **Confidence Scoring** — Provides a heuristic confidence percentage for the suggested message
- **Mixed Change Detection** — Warns when staged changes span multiple unrelated concerns
- **Clipboard Integration** — Automatically copies the generated message for quick pasting
- **Multiple CLI Modes** — Default, `--analyze`, `--dry-run`, and `--suggest` modes
- **Project Configuration** — Optional `.gitmsg/config.toml` for per-project settings
- **Fully Offline** — No API keys, no network calls, no external AI dependencies

---

## Installation

Requires **Python 3.11+** and **Git** installed.

### From GitHub

```bash
pip install git+https://github.com/Jingjing-20/gitmsg.git
```

### From Source

```bash
git clone https://github.com/Jingjing-20/gitmsg.git
cd gitmsg
pip install -e .
```

### Verify Installation

```bash
python -m gitmsg --version
```

---

## Usage

Stage your changes first, then run GitMsg from anywhere inside the repository:

```bash
git add .
python -m gitmsg
```

### Example Output

```text
Analyzing staged changes...

Files changed: 1
Insertions: +2
Deletions: -0

Detected changes:
  • Add project filtering

Change type: feat
Scope: projects
Confidence: 78%

Suggested commit:

  feat(projects): add project filtering

✓ Copied to clipboard
```

Then commit with the suggested message:

```bash
git commit -m "feat(projects): add project filtering"
```

### CLI Commands

| Command | Behavior |
| --- | --- |
| `python -m gitmsg` | Analyze staged changes, suggest a message, copy it |
| `python -m gitmsg --version` | Show the version |
| `python -m gitmsg --help` | Show help |
| `python -m gitmsg --analyze` | Show analysis only (no generated message, no copy) |
| `python -m gitmsg --dry-run` | Generate and display a message without copying |
| `python -m gitmsg --suggest` | Show alternative messages when they are useful |
| `python -m gitmsg init` | Create optional `.gitmsg/config.toml` |

---

## Configuration

Normal usage does not require initialization.

```bash
python -m gitmsg init
```

Creates `.gitmsg/config.toml` with optional settings:

```toml
[gitmsg]
max_message_length = 72
copy_to_clipboard = true
default_scope = ""
```

---

## Built With

- **Python** — Programming language
- **Typer** — CLI framework
- **Rich** — Terminal UI and formatting
- **Pyperclip** — Clipboard integration
- **Git CLI** — Git integration via `subprocess`
- **pytest** — Testing framework
- **Ruff** — Linter and formatter

---

## Architecture

```text
src/gitmsg/
  cli.py          CLI commands, output, modes
  git.py          Repository detection and Git CLI
  diff.py         Staged diff parsing and statistics
  analyzer.py     Categories, signals, mixed-change notice
  classifier.py   Conventional Commit type, scope, confidence
  generator.py    Imperative message formatting
  clipboard.py    Clipboard copy with graceful failure
  config.py       Optional .gitmsg/config.toml
  models.py       Dataclasses
  exceptions.py   Expected application errors
```
