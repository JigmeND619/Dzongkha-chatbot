"""Free machine translation via Google Translate's public web endpoint (no API key).
This is an UNOFFICIAL endpoint: it can change, be rate-limited, or be blocked, and its terms may
restrict heavy use. Fine for personal learning; use the official Cloud Translation API for real products."""
import json
import urllib.error
import urllib.parse
import urllib.request

from .errors import TranslationError

ENDPOINT = "https://translate.googleapis.com/translate_a/single"
MAX_CHUNK = 1500  # characters per request


def _chunks(text):
    """Split on line breaks into pieces no longer than MAX_CHUNK."""
    pieces, current = [], ""
    for line in text.split("\n"):
        while len(line) > MAX_CHUNK:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(line[:MAX_CHUNK])
            line = line[MAX_CHUNK:]
        if current and len(current) + len(line) + 1 > MAX_CHUNK:
            pieces.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        pieces.append(current)
    return pieces


def _translate_chunk(text, source, target):
    body = urllib.parse.urlencode({"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text}).encode()
    request = urllib.request.Request(ENDPOINT, data=body, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        return "".join(part[0] for part in data[0] if part and part[0])
    except (urllib.error.URLError, TimeoutError, ValueError, IndexError, TypeError) as exc:
        raise TranslationError("translation request failed") from exc


def translate(text, source, target):
    return "\n".join(_translate_chunk(piece, source, target) for piece in _chunks(text)).strip()


def to_dzongkha(text):
    return translate(text, "en", "dz")


def to_english(text):
    return translate(text, "auto", "en")
