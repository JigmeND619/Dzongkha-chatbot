"""HTTP routes. Business logic lives in the other modules."""
import uuid

from flask import Blueprint, current_app, jsonify, render_template, request, session

from .config import MAX_MESSAGE_CHARS, get_dzongkha_mode
from .errors import RequestError, describe_error
from .pipeline import run_translate_pipeline
from .validation import validate_chat_request

bp = Blueprint("main", __name__)


def error_response(message, status):
    return jsonify({"error": message}), status


def session_id():
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return session["sid"]


@bp.get("/")
def index():
    return render_template("index.html", max_chars=MAX_MESSAGE_CHARS)


@bp.post("/api/chat")
def chat():
    llm, store = current_app.extensions["llm"], current_app.extensions["history"]
    sid = session_id()
    try:
        message, show_translation, verify = validate_chat_request(request.get_json(silent=True))
        if get_dzongkha_mode() == "translate":
            result, remember_user, remember_reply = run_translate_pipeline(
                llm, store.recent(sid), message, show_translation)
            verified = False
        else:
            result, verified = llm.reply(store.recent(sid), message, show_translation, verify)
            remember_user, remember_reply = message, result["dzongkha"]
    except RequestError as exc:
        return error_response(exc.message, exc.status)
    except Exception as exc:  # known errors get friendly messages; unknown ones are re-raised
        described = describe_error(exc)
        if described is None:
            raise
        return error_response(*described)

    store.add_exchange(sid, remember_user, remember_reply)
    result["verified_by_self_review"] = verified
    return jsonify(result)


@bp.post("/api/clear")
def clear():
    current_app.extensions["history"].clear(session_id())
    return jsonify({"status": "cleared"})
