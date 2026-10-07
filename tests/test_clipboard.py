from __future__ import annotations

from gitmsg.clipboard import copy_text


def test_copy_text_success(monkeypatch) -> None:
    copied: list[str] = []

    def fake_copy(text: str) -> None:
        copied.append(text)

    monkeypatch.setattr("gitmsg.clipboard.pyperclip.copy", fake_copy)
    assert copy_text("feat: add filtering") is True
    assert copied == ["feat: add filtering"]


def test_copy_text_failure(monkeypatch) -> None:
    def fake_copy(_text: str) -> None:
        raise RuntimeError("clipboard unavailable")

    monkeypatch.setattr("gitmsg.clipboard.pyperclip.copy", fake_copy)
    assert copy_text("feat: add filtering") is False
