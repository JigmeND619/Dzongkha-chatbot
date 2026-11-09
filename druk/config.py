"""Settings. Secrets are read from the environment (.env) and never leave the server."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
# Load .env from the project folder explicitly. override=True so an empty OPENAI_API_KEY
# already set in Windows/PowerShell cannot hide the value in the file.
load_dotenv(ENV_FILE, override=True, encoding="utf-8-sig")
MAX_MESSAGE_CHARS = 2000      # longest user message accepted
MAX_REQUEST_BYTES = 16 * 1024  # request size limit
MAX_HISTORY_MESSAGES = 10     # recent messages sent to the model (cost + context limit)
MAX_SESSIONS = 500            # oldest in-memory conversations are dropped beyond this


def get_api_key():
    return os.getenv("OPENAI_API_KEY", "").strip()


def get_model():
    # Strip spaces and accidental quotes, e.g. OPENAI_MODEL="gemini-2.5-flash "
    return os.getenv("OPENAI_MODEL", "gpt-4o").strip().strip("\"'").strip() or "gpt-4o"


def get_base_url():
    """Optional: point the OpenAI SDK at another OpenAI-compatible service (e.g. Gemini, Ollama)."""
    return os.getenv("OPENAI_BASE_URL", "").strip() or None


def json_mode_enabled():
    """Ask the API to force JSON output. Set JSON_MODE=false if a provider rejects it."""
    return os.getenv("JSON_MODE", "true").strip().lower() not in ("false", "0", "no")


def get_dzongkha_mode():
    """'llm' = the model writes Dzongkha itself. 'translate' = the model answers in English and a
    free translation service converts it to Dzongkha (works with weak/free models)."""
    return "translate" if os.getenv("DZONGKHA_MODE", "llm").strip().lower() == "translate" else "llm"


def get_secret_key():
    return os.getenv("FLASK_SECRET_KEY") or os.urandom(24)


def env_help():
    """Plain-English hint about why the key is missing (also printed to the server console)."""
    if (BASE_DIR / ".env.txt").exists() and not ENV_FILE.exists():
        return "Found '.env.txt'. Rename it to exactly '.env' (turn on 'File name extensions' in Explorer)."
    if not ENV_FILE.exists():
        return f"No .env file at {ENV_FILE}. Copy .env.example to .env."
    if get_api_key() == "your-api-key-here":
        return ".env still contains the placeholder key. Paste your real key after OPENAI_API_KEY=."
    return "A .env file exists but OPENAI_API_KEY is empty or misspelled. Use: OPENAI_API_KEY=sk-... (no quotes, no spaces)."
