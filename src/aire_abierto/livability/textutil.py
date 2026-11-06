"""Shared name cleaning for joins across INEGI, CONAPO, and ENSU."""

from __future__ import annotations

import unicodedata


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_name(value: str) -> str:
    text = strip_accents(value or "").lower().replace("\n", " ")
    text = text.replace("gral.", "general")
    for token in (", cdmx", " cdmx"):
        if text.endswith(token):
            text = text[: -len(token)]
    text = text.replace("- ", "-").replace(" -", "-")
    text = " ".join(text.replace(".", " ").split())
    return text
