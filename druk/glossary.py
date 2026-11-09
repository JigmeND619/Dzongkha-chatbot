"""Verified-glossary hook. Only add entries checked by a fluent speaker or an official source."""
import json

from .config import BASE_DIR


def load_glossary():
    try:
        data = json.loads((BASE_DIR / "glossary.json").read_text(encoding="utf-8"))
        return [e for e in data.get("entries", []) if e.get("english") and e.get("dzongkha")]
    except (OSError, ValueError):
        return []
