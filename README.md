# GitMsg

> A local-first Python CLI that analyzes staged Git changes and generates meaningful Conventional Commit messages.

GitMsg helps developers turn staged changes into concise, useful commit messages without automatically creating the commit.

## Motivation

Writing a good commit message is easier after the change is already staged, but `git commit` still asks for the message first. GitMsg inspects the staged diff, classifies the change, and suggests a Conventional Commit so you can paste or type it yourself.

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

After staging a new function such as `add_project_filtering` in `src/projects.py`:

```text
GitMsg

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

GitMsg does **not** automatically create the Git commit. The developer remains in control:

```bash
git commit -m "feat(projects): add project filtering"
```

## Features

- Analyze staged Git changes only (`git diff --cached`)
- Detect added, modified, deleted, renamed, and copied files
- Analyze file types and change signals
- Classify changes using Conventional Commits
- Detect scope when the paths are consistent enough
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

Requires Python 3.11+ and Git on PATH.

Development installation:

```bash
pip install -e .
```

Then:

```bash
gitmsg --help
gitmsg --version
```

On Windows, if `gitmsg` is not found, either add your user Scripts directory to PATH or run:

```bash
python -m gitmsg --help
```

## Basic usage

Stage your changes first:

```bash
git add .
```

Then run GitMsg from anywhere inside the repository:

```bash
gitmsg
```

If nothing is staged:

```text
No staged changes found.

Stage your changes first:

  git add <files>
```

## CLI commands

| Command | Behavior |
| --- | --- |
| `gitmsg` | Analyze staged changes, suggest a message, copy it |
| `gitmsg --help` | Show help |
| `gitmsg --version` | Show the version |
| `gitmsg --analyze` | Show analysis only (no generated message, no copy) |
| `gitmsg --dry-run` | Generate and display a message without copying |
| `gitmsg --suggest` | Show alternative messages when they are useful |
| `gitmsg init` | Create optional `.gitmsg/config.toml` |

`--suggest` prints multiple candidates when scoring is close. In an interactive terminal you can select one; otherwise GitMsg uses the first suggestion.

## Configuration

Normal usage does not require initialization.

```bash
gitmsg init
```

creates:

```text
.gitmsg/config.toml
```

and adds `.gitmsg/` to `.gitignore` if it is missing.

Example:

```toml
[gitmsg]
max_message_length = 72
copy_to_clipboard = true
default_scope = ""
```

- `max_message_length`: integer from 8 to 200
- `copy_to_clipboard`: `true` or `false`
- `default_scope`: optional scope used when inference is empty

Malformed configuration produces an actionable error instead of a traceback.

## Architecture

```text
src/gitmsg/
  cli.py          CLI commands, output, modes
  git.py          repository detection and Git CLI
  diff.py         staged diff parsing and statistics
  analyzer.py     categories, signals, mixed-change notice
  classifier.py   Conventional Commit type, scope, confidence
  generator.py    imperative message formatting
  clipboard.py    clipboard copy with graceful failure
  config.py       optional .gitmsg/config.toml
  models.py       dataclasses
  exceptions.py   expected application errors
```

## Development

Quality checks:

```bash
pytest
ruff check .
python -m compileall src
```

Install with development extras:

```bash
pip install -e ".[dev]"
```

## Testing

Tests cover repository detection, staged diffs, analysis, classification, generation, clipboard failure, CLI modes, configuration, and Git integration using temporary repositories.

```bash
pytest
```

## Limitations

- Classification is deterministic and heuristic, not statistically calibrated.
- GitMsg does not understand every language or every kind of change.
- Mixed staged changes are reported; GitMsg never unstages, resets, or splits commits.
- Clipboard access can fail depending on the desktop environment.
- The MVP does not call any external AI/LLM API.

## Roadmap

- Keep improving signal quality and scope inference
- Optional local LLM refinement after the deterministic engine (not required)

## License

MIT
