"""Shape-coercion helpers for GPT-4o JSON output.

Model responses are merged into deterministic baselines throughout the AI services.
A field with the wrong shape (a string where an array was expected, null where text
was expected, ...) must fall back to the deterministic value for THAT FIELD ONLY —
never crash the request and never discard the rest of the response.
"""

from __future__ import annotations

from typing import Any


def as_str_list(value: Any, fallback: list[str]) -> list[str]:
    """Coerce a model field into a list[str]. A bare string becomes a one-item list
    (never character-split). None or an unusable value returns the fallback."""
    if value is None:
        return list(fallback)
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else list(fallback)
    if isinstance(value, (list, tuple)):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned if cleaned else list(fallback)
    return list(fallback)


def as_dict_list(value: Any, fallback: list[dict]) -> list[dict]:
    """Coerce a model field into a list[dict], dropping non-dict entries. None or an
    unusable value returns the fallback."""
    if isinstance(value, (list, tuple)):
        cleaned = [item for item in value if isinstance(item, dict)]
        return cleaned if cleaned else list(fallback)
    return list(fallback)


def as_text(value: Any, fallback: str) -> str:
    """Coerce a model field into a non-empty string. None, an empty/blank string, or
    any non-string value returns the fallback."""
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else fallback
    return fallback
