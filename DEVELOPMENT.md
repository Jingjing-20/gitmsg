# Development Guide

Guide for developers working on GitMsg.

## Table of Contents

- [Development Setup](#development-setup)
- [Architecture](#architecture)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Code Style](#code-style)
- [Release Process](#release-process)

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Virtual environment tool (venv or virtualenv)
- pip or uv

### Initial Setup

```bash
# Clone repository
git clone https://github.com/Jingjing-20/gitmsg.git
cd gitmsg

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check version
python -m gitmsg --version

# Run tests
pytest

# Run linter
ruff check .
```

## Architecture

### Module Overview

```
src/gitmsg/
├── cli.py          # Entry point, CLI commands, user interface
├── git.py          # Git repository detection, subprocess calls
├── diff.py         # Parse git diff output, extract statistics
├── analyzer.py     # Analyze changes, detect patterns
├── classifier.py   # Classify commit type and scope
├── generator.py    # Generate commit message text
├── clipboard.py    # Clipboard integration
├── config.py       # Configuration loading
├── models.py       # Data classes
└── exceptions.py   # Custom exceptions
```

### Data Flow

```
1. cli.py
   ↓ calls
2. git.py → Check repository, get staged diff
   ↓ passes diff content
3. diff.py → Parse diff, extract stats
   ↓ passes parsed data
4. analyzer.py → Analyze file changes, detect patterns
   ↓ passes analysis
5. classifier.py → Determine type and scope
   ↓ passes classification
6. generator.py → Format commit message
   ↓ passes message
7. clipboard.py → Copy to clipboard
   ↓ returns
8. cli.py → Display to user
```

### Core Classes

#### `DiffStats` (models.py)

```python
@dataclass
class DiffStats:
    """Statistics from git diff."""
    files_changed: int
    insertions: int
    deletions: int
    added_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]
    renamed_files: list[tuple[str, str]]
```

#### `ChangeAnalysis` (models.py)

```python
@dataclass
class ChangeAnalysis:
    """Analysis of staged changes."""
    primary_category: str
    confidence: float
    scope: str | None
    mixed_changes: bool
    change_summary: str
```

#### `CommitClassification` (models.py)

```python
@dataclass
class CommitClassification:
    """Commit classification result."""
    type: CommitType
    scope: str | None
    subject: str
    confidence: float
```

## Development Workflow

### Creating a Feature

```bash
# 1. Create branch
git checkout -b feat/your-feature-name

# 2. Make changes
# Edit files...

# 3. Test frequently
pytest tests/test_your_feature.py

# 4. Run full test suite
pytest

# 5. Check code style
ruff check --fix .
ruff format .

# 6. Commit with conventional commit
git commit -m "feat(module): add feature description"

# 7. Push and create PR
git push origin feat/your-feature-name
```

### Testing Locally

```bash
# Install in editable mode
pip install -e .

# Test in a real repository
cd /path/to/test/repo

# Make some changes
echo "test" > test.txt
git add test.txt

# Run GitMsg
python -m gitmsg

# Or use installed command
gitmsg
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gitmsg --cov-report=html

# Run specific test file
pytest tests/test_classifier.py

# Run specific test
pytest tests/test_classifier.py::test_feat_detection

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Writing Tests

#### Unit Tests

```python
# tests/test_classifier.py
import pytest
from gitmsg.classifier import classify_commit_type
from gitmsg.models import ChangeAnalysis

def test_feat_classification():
    """Test new feature classification."""
    analysis = ChangeAnalysis(
        added_files=["src/new_module.py"],
        primary_category="implementation",
        confidence=0.8,
    )
    
    result = classify_commit_type(analysis)
    
    assert result.type == "feat"
    assert result.confidence > 0.7
```

#### Integration Tests

```python
# tests/test_integration.py
import subprocess
from pathlib import Path

def test_full_workflow(tmp_path):
    """Test complete GitMsg workflow."""
    # Setup test repository
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    subprocess.run(["git", "init"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_dir)
    
    # Create and stage file
    test_file = repo_dir / "test.py"
    test_file.write_text("def test(): pass")
    subprocess.run(["git", "add", "test.py"], cwd=repo_dir)
    
    # Run GitMsg
    result = subprocess.run(
        ["python", "-m", "gitmsg", "--dry-run"],
        cwd=repo_dir,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "feat" in result.stdout or "chore" in result.stdout
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=gitmsg --cov-report=html

# View report
# Open htmlcov/index.html in browser

# Target: >80% coverage
```

## Debugging

### Debug Mode

Add logging for development:

```python
# In any module
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"Analysis result: {analysis}")
```

### VSCode Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: GitMsg",
      "type": "python",
      "request": "launch",
      "module": "gitmsg",
      "args": ["--dry-run"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/test_repo"
    },
    {
      "name": "Python: Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Common Debugging Tasks

**1. Debug diff parsing:**
```python
from gitmsg.diff import parse_diff

diff_content = """
diff --git a/file.py b/file.py
new file mode 100644
..."""

stats = parse_diff(diff_content)
print(stats)
```

**2. Debug classification:**
```python
from gitmsg.classifier import classify_commit_type
from gitmsg.models import ChangeAnalysis

analysis = ChangeAnalysis(...)
result = classify_commit_type(analysis)
print(f"Type: {result.type}, Confidence: {result.confidence}")
```

**3. Test Git operations:**
```python
from gitmsg.git import get_staged_diff

try:
    diff = get_staged_diff()
    print(diff)
except Exception as e:
    print(f"Error: {e}")
```

## Code Style

### Linting and Formatting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check specific file
ruff check src/gitmsg/classifier.py
```

### Ruff Configuration

In `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
]
```

### Type Checking (Optional)

```bash
# Install mypy
pip install mypy

# Run type checker
mypy src/gitmsg

# Ignore errors temporarily
# type: ignore
```

## Release Process

### Version Bumping

1. Update version in `pyproject.toml`:
   ```toml
   [project]
   version = "0.2.0"
   ```

2. Update `CHANGELOG.md`:
   ```markdown
   ## [0.2.0] - 2026-10-15
   
   ### Added
   - Feature X
   
   ### Fixed
   - Bug Y
   ```

3. Commit changes:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 0.2.0"
   ```

### Creating a Release

```bash
# Tag the release
git tag -a v0.2.0 -m "Release v0.2.0"

# Push tag to GitHub
git push origin v0.2.0

# GitHub Actions can automate PyPI publishing
```

### Building Distribution

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Check distribution
twine check dist/*

# Upload to PyPI (requires credentials)
twine upload dist/*
```

## Performance Profiling

### Basic Profiling

```python
import time

start = time.time()
result = expensive_function()
print(f"Time: {time.time() - start:.2f}s")
```

### cProfile

```bash
# Profile script
python -m cProfile -s tottime -m gitmsg > profile.txt

# Analyze results
less profile.txt
```

## Tips and Best Practices

### Development Tips

1. **Test early, test often**
   - Write tests before or alongside code
   - Run tests frequently

2. **Use type hints**
   - Makes code self-documenting
   - Catches errors early

3. **Keep functions small**
   - Single responsibility
   - Easy to test

4. **Handle errors gracefully**
   - Use custom exceptions
   - Provide helpful error messages

### Git Tips

```bash
# Amend last commit
git commit --amend

# Interactive rebase
git rebase -i HEAD~3

# Stash changes
git stash
git stash pop

# Show changes
git diff
git diff --staged
```

### Useful Commands

```bash
# Find TODOs
rg "TODO|FIXME" src/

# Count lines of code
tokei

# Check dependencies
pip list --outdated

# Show package info
pip show gitmsg
```

## Resources

- [Python Documentation](https://docs.python.org/3/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Getting Help

- Check [CONTRIBUTING.md](CONTRIBUTING.md)
- Open a discussion on GitHub
- Review existing issues
- Read the source code

Happy coding! 🚀
