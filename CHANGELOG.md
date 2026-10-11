# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-11

### Added

- **Multi-change commit descriptions.** When multiple non-vague change summaries are detected, the generated commit description now combines them instead of using only the first one. Summaries sharing a leading verb collapse into a single `verb a, b, c` phrase (e.g. `feat(core): update alpha, beta, gamma`). When the combined text exceeds the configured length budget, an `and more` suffix is appended so omitted changes are still signaled.
- **Descriptive file labels for short stems.** Files with short stems (≤ 6 characters) now include their parent directory in the label when the parent is meaningful (e.g. `data/deployed.json` → `deployed data` instead of just `deployed`).

### Changed

- `update staged changes` is now treated as a vague fallback and skipped when a more specific summary is available.

## [0.1.0] - 2026-10-11

### Added

- Initial release.
- Staged diff parsing and statistics.
- Conventional Commit classification with type, scope, and confidence.
- Imperative commit message generation with length limits.
- Clipboard integration with graceful failure.
- CLI modes: default, `--analyze`, `--dry-run`, `--suggest`.
- Optional `.gitmsg/config.toml` project configuration via `gitmsg init`.
- Mixed-change detection.
