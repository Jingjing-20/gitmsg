# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in GitMsg, please report it by emailing or opening a private security advisory on GitHub.

**Please do not report security vulnerabilities through public GitHub issues.**

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Notes

- GitMsg runs entirely locally with no network calls
- No external APIs or AI services are used
- Git operations use subprocess with proper input sanitization
- Clipboard access is opt-in and can be disabled in config
