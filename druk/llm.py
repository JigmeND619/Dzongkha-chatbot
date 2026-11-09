"""Everything that talks to OpenAI (official SDK, Chat Completions in JSON mode)."""
import json

from openai import OpenAI

import logging

from .config import env_help, get_api_key, get_base_url, get_model, json_mode_enabled
from .errors import ConfigError, ModelOutputError, NotDzongkhaError
from .prompts import ENGLISH_PROMPT, VERIFY_PROMPT, build_system_prompt
from .validation import parse_model_output


REMINDER = ('Your last reply was not written in Dzongkha script. The "dzongkha" field MUST be Dzongkha in '
            'Tibetan script (no English, no Latin letters). If you cannot, write a short Dzongkha apology '
            'or clarification request instead. Reply again with the same JSON format.')


class LLMService:
    def __init__(self, client=None):
        self._client = client  # tests inject a fake client here

    def _get_client(self):
        if self._client is None:
            key = get_api_key()
            if not key or key == "your-api-key-here":
                hint = env_help()
                logging.getLogger("druk_ai").error("API key missing: %s", hint)
                raise ConfigError("The server has no OpenAI API key configured. " + hint)
            self._client = OpenAI(api_key=key, base_url=get_base_url(), max_retries=2, timeout=60)
        return self._client

    def _call(self, messages, want_json=True):
        options = {}
        if want_json and json_mode_enabled():
            options["response_format"] = {"type": "json_object"}
        resp = self._get_client().chat.completions.create(
            model=get_model(), messages=messages, temperature=0.3, **options)
        return resp.choices[0].message.content

    def english_reply(self, recent_history, english_message):
        """Plain-text English answer (used by the translate pipeline)."""
        messages = [{"role": "system", "content": ENGLISH_PROMPT}] + recent_history
        messages.append({"role": "user", "content": english_message})
        return (self._call(messages, want_json=False) or "").strip()

    def reply(self, recent_history, message, show_translation, verify):
        """Return (result_dict, verified_flag). Raises ModelOutputError or OpenAI errors."""
        messages = [{"role": "system", "content": build_system_prompt(show_translation)}]
        messages += recent_history
        messages.append({"role": "user", "content": message})
        try:
            result = parse_model_output(self._call(messages), show_translation)
        except NotDzongkhaError:
            # One retry with a firmer reminder; if it fails again the error is shown to the user.
            messages.append({"role": "system", "content": REMINDER})
            result = parse_model_output(self._call(messages), show_translation)
        if not verify:
            return result, False

        review = [
            {"role": "system", "content": VERIFY_PROMPT + build_system_prompt(show_translation)},
            {"role": "user", "content": json.dumps({"user_message": message, "draft": result},
                                                   ensure_ascii=False)},
        ]
        try:
            return parse_model_output(self._call(review), show_translation), True
        except ModelOutputError:
            # Keep the original draft but disclose that the review failed.
            result["uncertain"] = True
            result["uncertainty_note"] = (
                result["uncertainty_note"] + " The automatic self-review could not be completed."
            ).strip()
            return result, False
