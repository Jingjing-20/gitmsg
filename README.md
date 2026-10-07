# GitMsg

> A local-first Python CLI that analyzes staged Git changes and generates meaningful Conventional Commit messages.

GitMsg helps developers turn staged changes into concise, useful commit messages without automatically creating the commit.

## How it works

```text
Git staged changes
       ↓
GitMsg
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

## Example

```text
GitMsg

Analyzing staged changes...

Files changed: 3
Insertions: +54
Deletions: -12

Detected changes:
  • Added project filtering
  • Added category state
  • Updated project rendering

Change type: feat
Scope: projects
Confidence: 93%

Suggested commit:

  feat(projects): add project filtering

✓ Copied to clipboard
```

GitMsg does **not** automatically create the Git commit. The developer remains in control:

```bash
git commit -m "feat(projects): add project filtering"
```

## Features

- Analyze staged Git changes
- Detect added, modified, deleted, and renamed files
- Analyze file types and change signals
- Classify changes using Conventional Commits
- Detect scope when confidence is sufficient
- Provide a heuristic confidence score
- Detect potentially mixed changes
- Copy generated messages to the clipboard
- Work locally without an external AI/LLM service
- Support `--analyze`, `--dry-run`, and `--suggest` modes
- Optional project configuration through `.gitmsg/config.toml`

## Technology

- Python 3.11+
- Git
- Typer
- Rich
- Pyperclip
- pytest
- Ruff

GitMsg uses the Git CLI through Python's `subprocess` rather than requiring GitPython.

## Installation

Development installation:

```bash
pip install -e .
```

Then:

```bash
gitmsg
```

## Basic usage

Stage your changes first:

```bash
git add .
```

Then run:

```bash
gitmsg
```

Other modes:

```bash
gitmsg --help
gitmsg --version
gitmsg --analyze
gitmsg --dry-run
gitmsg --suggest
gitmsg init
```

## Local-first and deterministic

The MVP does not require OpenAI, Anthropic, Gemini, OpenRouter, or another hosted LLM.

The core analysis and message generation are designed to work locally and deterministically.

An optional AI/LLM layer may be considered in the future for message refinement, but it is not required for GitMsg to function.

## Development

GitMsg is developed incrementally with the following workflow:

```text
INSPECT
   ↓
PLAN
   ↓
IMPLEMENT
   ↓
TEST
   ↓
REVIEW
   ↓
FIX
   ↓
VERIFY
   ↓
COMMIT
   ↓
PUSH
```

Quality checks:

```bash
pytest
ruff check .
python -m compileall src
```

## Project status

The installable `gitmsg` CLI currently supports `--help` and `--version`. Repository analysis is still being implemented.

GitMsg is being developed as a production-quality MVP with an emphasis on:

- simple architecture
- deterministic behavior
- realistic Git integration
- useful analysis rather than vague commit messages
- strong test coverage
- safe Git operations
- Windows compatibility

## License

MIT
