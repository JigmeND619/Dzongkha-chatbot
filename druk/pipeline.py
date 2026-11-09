"""Translate mode: (Dzongkha -> English) -> free LLM answers in English -> (English -> Dzongkha)."""
from .errors import ModelOutputError, TranslationError
from .translator import to_dzongkha, to_english
from .validation import looks_like_dzongkha_script

NOTE = "Machine-translated from English by a free translation service; it may contain mistakes."


def has_tibetan(text):
    return any("\u0f00" <= c <= "\u0fff" for c in text)


def run_translate_pipeline(llm, recent_history, message, show_translation):
    """Return (result, english_question, english_answer). The English pair is what we remember."""
    english_question = to_english(message) if has_tibetan(message) else message
    if not english_question:
        raise TranslationError("empty translation")
    english_answer = llm.english_reply(recent_history, english_question)
    if not english_answer:
        raise ModelOutputError("empty answer")
    dzongkha = to_dzongkha(english_answer)
    if not looks_like_dzongkha_script(dzongkha):
        raise TranslationError("result is not Dzongkha script")
    result = {
        "dzongkha": dzongkha,
        "english_translation": english_answer if show_translation else None,
        "uncertain": True,  # always flagged: machine translation is never verified
        "uncertainty_note": NOTE,
    }
    return result, english_question, english_answer
