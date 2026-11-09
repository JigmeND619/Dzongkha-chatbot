"""In-memory conversation history, one list per browser session. Nothing is saved to disk."""
from .config import MAX_HISTORY_MESSAGES, MAX_SESSIONS


class HistoryStore:
    def __init__(self):
        self._sessions = {}

    def get(self, sid):
        if sid not in self._sessions:
            while len(self._sessions) >= MAX_SESSIONS:
                self._sessions.pop(next(iter(self._sessions)))  # drop the oldest
            self._sessions[sid] = []
        return self._sessions[sid]

    def recent(self, sid):
        return list(self.get(sid)[-MAX_HISTORY_MESSAGES:])

    def add_exchange(self, sid, user_text, assistant_text):
        """Store only the Dzongkha reply (keeps history small and consistent)."""
        history = self.get(sid)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": assistant_text})
        del history[:-MAX_HISTORY_MESSAGES * 2]

    def clear(self, sid):
        self.get(sid).clear()
