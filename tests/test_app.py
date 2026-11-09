"""Backend tests. The OpenAI client is faked, so no API credits are used.
These tests check software behaviour, NOT the linguistic accuracy of Dzongkha."""
import json
import os
import sys
from types import SimpleNamespace

import httpx
import openai
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402

SECRET = "sk-test-SECRET-123"
REQ = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


def good(dz="ཐིམ་ཕུ།", en="Thimphu.", **extra):
    body = {"dzongkha": dz, "english_translation": en, "uncertain": False, "uncertainty_note": ""}
    body.update(extra)
    return json.dumps(body, ensure_ascii=False)


class FakeClient:
    """Returns queued replies (strings) or raises queued exceptions; records every call."""
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=item))])


def make(*replies):
    fake = FakeClient(*replies)
    app = create_app(client=fake)
    return app.test_client(), fake


def post(client, **payload):
    return client.post("/api/chat", json=payload)


@pytest.mark.parametrize("msg", ["", "   ", None, 5])
def test_empty_or_invalid_message_rejected(msg):
    client, fake = make()
    assert post(client, message=msg).status_code == 400
    assert fake.calls == []


def test_malformed_body_rejected():
    client, _ = make()
    assert client.post("/api/chat", data="not json", content_type="text/plain").status_code == 400


def test_too_long_message_rejected():
    client, _ = make()
    assert post(client, message="a" * 5000).status_code == 413


@pytest.mark.parametrize("text", ["What is the capital of Bhutan?", "ཀུ་ཟུ་ཟང་པོ་ལགས།", "Please say ཀུ་ཟུ་ཟང་པོ་ལགས། in English"])
def test_english_dzongkha_and_mixed_input(text):
    client, fake = make(good())
    res = post(client, message=text)
    assert res.status_code == 200
    assert res.get_json()["dzongkha"] == "ཐིམ་ཕུ།"
    assert fake.calls[0]["messages"][-1]["content"] == text


def test_translation_disabled_returns_no_english():
    client, _ = make(good())
    assert post(client, message="hi", show_translation=False).get_json()["english_translation"] is None


def test_translation_enabled_returns_english():
    client, fake = make(good())
    data = post(client, message="hi", show_translation=True).get_json()
    assert data["english_translation"] == "Thimphu."
    assert "did not request English" not in fake.calls[0]["messages"][0]["content"]


def test_translation_requested_but_missing_is_error():
    client, _ = make(good(en=""))
    assert post(client, message="hi", show_translation=True).status_code == 502


@pytest.mark.parametrize("bad", ["not json", "[]", json.dumps({"dzongkha": ""}), json.dumps({"x": 1})])
def test_invalid_model_output(bad):
    client, _ = make(bad)
    res = post(client, message="hi")
    assert res.status_code == 502
    assert bad not in res.get_data(as_text=True)  # raw output never shown


@pytest.mark.parametrize("exc,status", [
    (openai.AuthenticationError("x", response=httpx.Response(401, request=REQ), body=None), 401),
    (openai.RateLimitError("x", response=httpx.Response(429, request=REQ), body=None), 429),
    (openai.APITimeoutError(request=REQ), 504),
    (openai.APIConnectionError(request=REQ), 503),
    (openai.InternalServerError("x", response=httpx.Response(500, request=REQ), body=None), 502),
])
def test_openai_errors_mapped(exc, status):
    client, _ = make(exc)
    assert post(client, message="hi").status_code == status


def test_history_is_remembered_and_cleared():
    client, fake = make(good(dz="དང་པོ།"), good(dz="གཉིས་པ།"), good())
    post(client, message="Explain machine learning")
    post(client, message="Give me an example")
    roles = [m["role"] for m in fake.calls[1]["messages"]]
    assert roles == ["system", "user", "assistant", "user"]
    assert fake.calls[1]["messages"][1]["content"] == "Explain machine learning"
    client.post("/api/clear")
    post(client, message="new")
    assert len(fake.calls[2]["messages"]) == 2  # system + new user only


def test_history_is_isolated_between_sessions():
    fake = FakeClient(good(), good())
    app = create_app(client=fake)
    post(app.test_client(), message="secret topic")
    post(app.test_client(), message="other user")
    assert all("secret topic" not in m["content"] for m in fake.calls[1]["messages"])


def test_verify_mode_runs_second_call():
    client, fake = make(good(), good(dz="བསྐྱར་ཞིབ།"))
    data = post(client, message="hi", verify=True).get_json()
    assert len(fake.calls) == 2 and data["dzongkha"] == "བསྐྱར་ཞིབ།" and data["verified_by_self_review"]


def test_verify_failure_discloses_uncertainty():
    client, _ = make(good(), "garbage")
    data = post(client, message="hi", verify=True).get_json()
    assert data["uncertain"] is True and not data["verified_by_self_review"]


def test_api_key_never_exposed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", SECRET)
    client, _ = make(openai.AuthenticationError("bad", response=httpx.Response(401, request=REQ), body=None))
    pages = [client.get("/").get_data(as_text=True),
             client.get("/static/js/main.js").get_data(as_text=True),
             client.get("/static/js/api.js").get_data(as_text=True),
             post(client, message="hi").get_data(as_text=True)]
    assert all(SECRET not in p and "OPENAI_API_KEY" not in p for p in pages)


def test_missing_key_gives_clean_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    res = create_app().test_client().post("/api/chat", json={"message": "hi"})
    assert res.status_code == 500 and "API key" in res.get_json()["error"]
