"""Druk AI application factory."""
from flask import Flask

from .config import MAX_REQUEST_BYTES, get_secret_key
from .history import HistoryStore
from .llm import LLMService
from .routes import bp, error_response


def create_app(client=None):
    """Tests pass a fake `client`; normally the OpenAI client is built from the environment."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = get_secret_key()
    app.config.update(MAX_CONTENT_LENGTH=MAX_REQUEST_BYTES,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    app.extensions["llm"] = LLMService(client)
    app.extensions["history"] = HistoryStore()
    app.register_blueprint(bp)

    app.register_error_handler(413, lambda e: error_response("Request is too large.", 413))
    app.register_error_handler(404, lambda e: error_response("Not found.", 404))
    app.register_error_handler(405, lambda e: error_response("Method not allowed.", 405))
    return app
