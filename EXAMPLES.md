# GitMsg Examples

Real-world usage examples for GitMsg.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Common Scenarios](#common-scenarios)
- [Advanced Usage](#advanced-usage)
- [Edge Cases](#edge-cases)
- [Integration Examples](#integration-examples)

## Basic Usage

### Example 1: Adding a New Feature

```bash
# Create a new feature file
echo "def new_feature(): pass" > src/feature.py
git add src/feature.py

# Run GitMsg
python -m gitmsg
```

**Output:**
```
Analyzing staged changes...

Files changed: 1
Insertions: +1
Deletions: -0

Detected changes:
  • Add new feature implementation

Change type: feat
Scope: src
Confidence: 82%

Suggested commit:

  feat(src): add new feature implementation

✓ Copied to clipboard
```

**Commit:**
```bash
git commit -m "feat(src): add new feature implementation"
```

### Example 2: Fixing a Bug

```bash
# Fix a bug in existing file
echo "def fixed_function(): return True" > src/auth.py
git add src/auth.py

python -m gitmsg
```

**Output:**
```
Suggested commit:

  fix(auth): correct function return value

✓ Copied to clipboard
```

### Example 3: Updating Documentation

```bash
# Update README
echo "## New Section" >> README.md
git add README.md

python -m gitmsg
```

**Output:**
```
Suggested commit:

  docs(readme): add new section

✓ Copied to clipboard
```

## Common Scenarios

### Scenario 1: Multiple Files, Same Feature

```bash
# Add related files
touch src/api/users.py
touch src/api/auth.py
touch tests/test_api.py

git add src/api/ tests/

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Add user API
  • Add authentication API
  • Add API tests

Change type: feat
Scope: api
Confidence: 85%

Suggested commit:

  feat(api): add user and authentication endpoints

✓ Copied to clipboard
```

### Scenario 2: Refactoring Code

```bash
# Refactor without changing behavior
# Move functions, rename variables, restructure
git add src/refactored.py

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Refactor code structure

Change type: refactor
Scope: None
Confidence: 75%

Suggested commit:

  refactor: restructure code for clarity

✓ Copied to clipboard
```

### Scenario 3: Configuration Changes

```bash
# Update configuration
echo "DEBUG=False" >> .env
git add .env

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Update configuration

Change type: chore
Scope: config
Confidence: 70%

Suggested commit:

  chore(config): update environment settings

✓ Copied to clipboard
```

### Scenario 4: Dependency Updates

```bash
# Update dependencies
echo "requests==2.31.0" >> requirements.txt
git add requirements.txt

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Update dependencies

Change type: build
Scope: deps
Confidence: 90%

Suggested commit:

  build(deps): update requests to 2.31.0

✓ Copied to clipboard
```

### Scenario 5: Test Files Only

```bash
# Add tests
touch tests/test_new_feature.py
git add tests/

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Add tests

Change type: test
Scope: tests
Confidence: 95%

Suggested commit:

  test: add tests for new feature

✓ Copied to clipboard
```

## Advanced Usage

### Using --analyze Mode

```bash
# Show analysis without generating message
python -m gitmsg --analyze
```

**Output:**
```
Analyzing staged changes...

Files changed: 3
Insertions: +45
Deletions: -12

Added files:
  • src/api/users.py
  • src/api/auth.py

Modified files:
  • src/main.py

Detected patterns:
  • New API implementation
  • Authentication logic
  • Main entry point modification

Primary category: implementation
Confidence: 82%
Suggested scope: api

✓ Analysis complete
```

### Using --dry-run Mode

```bash
# Generate message but don't copy to clipboard
python -m gitmsg --dry-run
```

**Output:**
```
Suggested commit:

  feat(api): add user authentication

(Not copied to clipboard)
```

### Using --suggest Mode

```bash
# Show alternative commit messages
python -m gitmsg --suggest
```

**Output:**
```
Primary suggestion:

  feat(api): add user authentication

Alternative suggestions:

  feat(auth): implement user authentication
  feat(users): add user API with authentication
  feat: implement authentication API

Confidence: 82%
✓ Primary message copied to clipboard
```

## Edge Cases

### Mixed Changes

```bash
# Add feature + fix bug + update docs (not recommended)
echo "def new_feature(): pass" > src/feature.py
echo "def fixed_bug(): return True" > src/bugfix.py
echo "## Updates" >> README.md

git add .

python -m gitmsg
```

**Output:**
```
⚠️ Warning: Mixed changes detected

Your staged changes contain multiple unrelated modifications:
  • New feature
  • Bug fix
  • Documentation update

Consider splitting into separate commits:
  1. git reset
  2. git add src/feature.py
  3. git commit
  4. git add src/bugfix.py
  5. git commit
  6. git add README.md
  7. git commit

Suggested commit (if you must commit together):

  chore: multiple updates

Confidence: 45%
```

### Empty Commit Message Scope

```bash
# Changes in root directory
echo "print('hello')" > script.py
git add script.py

python -m gitmsg
```

**Output:**
```
Suggested commit:

  feat: add script

(No scope detected)
```

### Renamed Files

```bash
# Rename file
git mv old_name.py new_name.py
git add .

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Rename file

Change type: refactor
Scope: None
Confidence: 70%

Suggested commit:

  refactor: rename old_name to new_name

✓ Copied to clipboard
```

### Deleted Files

```bash
# Delete deprecated file
git rm deprecated.py
git add .

python -m gitmsg
```

**Output:**
```
Detected changes:
  • Remove deprecated code

Change type: chore
Scope: None
Confidence: 65%

Suggested commit:

  chore: remove deprecated code

✓ Copied to clipboard
```

## Integration Examples

### Git Hook Integration

Create `.git/hooks/prepare-commit-msg`:

```bash
#!/bin/bash

# Only run if no commit message provided
if [ -z "$2" ]; then
    # Get suggested message from GitMsg
    MESSAGE=$(python -m gitmsg --dry-run 2>/dev/null | grep -A 1 "Suggested commit:" | tail -n 1 | xargs)
    
    if [ -n "$MESSAGE" ]; then
        echo "$MESSAGE" > "$1"
    fi
fi
```

Make it executable:

```bash
chmod +x .git/hooks/prepare-commit-msg
```

Now `git commit` will pre-fill with GitMsg suggestion:

```bash
git add src/feature.py
git commit
# Editor opens with "feat(src): add feature" pre-filled
```

### CI/CD Integration

In GitHub Actions (`.github/workflows/validate-commits.yml`):

```yaml
name: Validate Commits

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install GitMsg
        run: pip install git+https://github.com/Jingjing-20/gitmsg.git
        
      - name: Check commit messages
        run: |
          # Validate all commits follow Conventional Commits
          git log --format=%s origin/main..HEAD | while read message; do
            if ! echo "$message" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?: .+'; then
              echo "Invalid commit message: $message"
              exit 1
            fi
          done
```

### Shell Alias

Add to `.bashrc` or `.zshrc`:

```bash
# Shortcut for GitMsg
alias gcm='python -m gitmsg && git commit -m "$(pbpaste)"'

# Or for Linux (using xclip)
alias gcm='python -m gitmsg && git commit -m "$(xclip -o -selection clipboard)"'
```

Usage:

```bash
git add .
gcm  # Analyzes, generates, copies, and commits!
```

### VS Code Task

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "GitMsg: Suggest Commit",
      "type": "shell",
      "command": "python -m gitmsg",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "GitMsg: Analyze",
      "type": "shell",
      "command": "python -m gitmsg --analyze",
      "problemMatcher": []
    }
  ]
}
```

Run via Command Palette: "Tasks: Run Task" → "GitMsg: Suggest Commit"

## Tips for Best Results

### 1. Stage Related Changes Together

```bash
# Good: Related changes
git add src/auth/ tests/auth/

# Bad: Unrelated changes
git add src/auth/ src/billing/ docs/
```

### 2. Use Descriptive File Names

```bash
# Good names help detection
src/user_authentication.py  # → feat(auth)
src/fix_login_bug.py       # → fix(login)

# Generic names provide less context
src/utils.py               # → chore
src/helpers.py             # → chore
```

### 3. Commit Atomic Changes

```bash
# One logical change per commit
git add src/feature.py tests/test_feature.py
python -m gitmsg
git commit

git add docs/feature.md
python -m gitmsg
git commit
```

### 4. Review Before Committing

```bash
# Always review the suggestion
python -m gitmsg --dry-run

# Adjust if needed
git commit -m "feat(auth): implement OAuth2 authentication"
```

## Troubleshooting Examples

### No Staged Changes

```bash
python -m gitmsg
```

**Output:**
```
Error: No staged changes found

Stage your changes first:
  git add <files>
```

### Not a Git Repository

```bash
cd /non-git-directory
python -m gitmsg
```

**Output:**
```
Error: Not a git repository

Initialize git first:
  git init
```

### Clipboard Error

```bash
python -m gitmsg
```

**Output:**
```
Suggested commit:

  feat(api): add endpoint

⚠️ Could not copy to clipboard (clipboard unavailable)
```

**Solution:** Use --dry-run and copy manually

---

For more examples and use cases, see the [README](README.md) and [CONTRIBUTING](CONTRIBUTING.md).
