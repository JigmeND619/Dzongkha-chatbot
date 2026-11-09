"""Checks for incoming requests and for the model's output."""
import json

from .config import MAX_MESSAGE_CHARS
from .errors import ModelOutputError, NotDzongkhaError, RequestError


def validate_chat_request(data):
    """Return (message, show_translation, verify) or raise RequestError."""
    if not isinstance(data, dict):
        raise RequestError("Send a JSON object.", 400)
    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        raise RequestError("Message cannot be empty.", 400)
    message = message.strip()
    if len(message) > MAX_MESSAGE_CHARS:
        raise RequestError(f"Message is too long (max {MAX_MESSAGE_CHARS} characters).", 413)
    # Only a real boolean true enables these options.
    return message, data.get("show_translation") is True, data.get("verify") is True


def _extract_json(raw):
    """Some providers wrap JSON in ```json fences or add text; keep only the outermost {...}."""
    text = raw.strip()
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if 0 <= start < end else text


def looks_like_dzongkha_script(text):
    """True if the text is mainly Tibetan-script (Dzongkha is written in it).
    Only checks the writing system, NOT whether the Dzongkha is correct."""
    tibetan = sum(1 for c in text if "\u0f00" <= c <= "\u0fff")
    other_letters = sum(1 for c in text if c.isalpha() and not "\u0f00" <= c <= "\u0fff")
    return tibetan > 0 and tibetan >= other_letters


def parse_model_output(raw, need_translation):
    """Validate the model's JSON. Raises ModelOutputError if unusable."""
    try:
        data = json.loads(_extract_json(raw))
    except (TypeError, ValueError) as exc:
        raise ModelOutputError("not valid JSON") from exc
    if not isinstance(data, dict):
        raise ModelOutputError("not an object")
    dz = data.get("dzongkha")
    if not isinstance(dz, str) or not dz.strip():
        raise ModelOutputError("missing dzongkha")
    if not looks_like_dzongkha_script(dz):
        raise NotDzongkhaError("reply is not in Tibetan script")
    en = data.get("english_translation", "")
    if not isinstance(en, str):
        raise ModelOutputError("bad translation")
    if need_translation and not en.strip():
        raise ModelOutputError("translation requested but missing")
    note = data.get("uncertainty_note", "")
    return {
        "dzongkha": dz.strip(),
        "english_translation": en.strip() if need_translation else None,
        "uncertain": data.get("uncertain") is True,
        "uncertainty_note": note.strip() if isinstance(note, str) else "",
    }
