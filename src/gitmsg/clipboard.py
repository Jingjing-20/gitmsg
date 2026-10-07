"""Copy generated commit messages to the clipboard."""

from __future__ import annotations

import pyperclip


def copy_text(text: str) -> bool:
    """Copy text to the clipboard.

    Returns True on success. Clipboard failures are not fatal.
    """
    try:
        pyperclip.copy(text)
    except Exception:
        return False
    return True
