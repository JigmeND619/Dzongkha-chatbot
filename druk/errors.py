"""Custom exceptions and the mapping from OpenAI errors to user-friendly HTTP responses."""
import logging

import openai

from .config import get_api_key, get_base_url, get_model

logger = logging.getLogger("druk_ai")


class RequestError(Exception):
    """The client sent a bad request (carries the HTTP status)."""
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


class ModelOutputError(Exception):
    """The model returned something we cannot safely show."""


class NotDzongkhaError(ModelOutputError):
    """The model answered, but not in Dzongkha (Tibetan) script."""


class TranslationError(Exception):
    """The free translation step failed."""


class ConfigError(Exception):
    """Server is missing required configuration."""


def _detail(exc):
    """Short provider message for the user, with the API key removed if it ever appears."""
    text = str(getattr(exc, "message", "") or exc)
    key = get_api_key()
    if key:
        text = text.replace(key, "[hidden]")
    return " ".join(text.split())[:300]


def _settings():
    """Non-secret settings the app is actually using (helps spot .env mistakes)."""
    return f" [model: '{get_model()}', base URL: '{get_base_url() or 'default OpenAI'}']"


def describe_error(exc):
    """Return (user_message, http_status) for a known error, or None if unknown."""
    if isinstance(exc, ConfigError):
        return str(exc), 500
    if isinstance(exc, TranslationError):
        logger.warning("Translation step failed")
        return ("The free translation service did not respond correctly. Check your internet "
                "connection and try again in a moment (it may be rate-limiting)."), 503
    if isinstance(exc, NotDzongkhaError):
        return ("The model replied, but not in Dzongkha script, even after a retry. This model probably "
                "cannot write Dzongkha reliably. Try a larger or hosted model (see OPENAI_MODEL in .env)."), 502
    if isinstance(exc, ModelOutputError):
        logger.warning("Model returned invalid output")
        return "The AI returned an unusable answer. Please try again.", 502
    if isinstance(exc, openai.AuthenticationError):
        logger.error("OpenAI authentication failed")
        return "The API key was rejected. Check OPENAI_API_KEY in your .env file.", 401
    if isinstance(exc, openai.RateLimitError):
        return "Rate limit or credit quota reached. Wait a moment or check billing.", 429
    if isinstance(exc, openai.APITimeoutError):  # must come before APIConnectionError
        return "The AI took too long to answer. Please try again.", 504
    if isinstance(exc, openai.APIConnectionError):
        return "Could not reach OpenAI. Check your internet connection.", 503
    if isinstance(exc, openai.NotFoundError):
        return "That model name was not found. Check OPENAI_MODEL (and OPENAI_BASE_URL) in .env." + _settings(), 404
    if isinstance(exc, (openai.BadRequestError, openai.PermissionDeniedError)):
        logger.error("AI service rejected the request status=%s detail=%s", exc.status_code, _detail(exc))
        return (f"The AI service rejected the request (status {exc.status_code}): {_detail(exc)} "
                "Check the API key, OPENAI_MODEL, OPENAI_BASE_URL and your region." + _settings()), exc.status_code
    if isinstance(exc, openai.APIStatusError):
        code = getattr(exc, "status_code", "?")
        logger.error("AI service error status=%s detail=%s", code, _detail(exc))
        return f"The AI service returned an error (status {code}): {_detail(exc)}", 502
    return None
