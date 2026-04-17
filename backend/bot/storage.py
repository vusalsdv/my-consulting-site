"""
Хранение истории диалогов + away mode + digest данные.
In-memory (всегда) + Supabase (если настроен).
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone

log = logging.getLogger(__name__)
MAX_HISTORY = 20


class ConversationStore:
    def __init__(self) -> None:
        self._history: dict[int, list[dict]] = defaultdict(list)
        self._meta: dict[int, dict] = {}   # chat_id -> {name, username, last_at, count}
        self.away: bool = False
        self._supabase = None
        self._try_init_supabase()

    def _try_init_supabase(self) -> None:
        try:
            from .config import SUPABASE_URL, SUPABASE_ANON_KEY
            if SUPABASE_URL and SUPABASE_ANON_KEY:
                from supabase import create_client
                self._supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                log.info("Supabase connected")
        except Exception as e:
            log.warning("Supabase unavailable: %s", e)

    # ── History ───────────────────────────────────────────────

    def get_history(self, chat_id: int) -> list[dict]:
        return list(self._history[chat_id])

    def add_message(self, chat_id: int, role: str, content: str) -> None:
        self._history[chat_id].append({"role": role, "content": content})
        if len(self._history[chat_id]) > MAX_HISTORY:
            self._history[chat_id] = self._history[chat_id][-MAX_HISTORY:]
        self._persist(chat_id, role, content)

    def is_new_user(self, chat_id: int) -> bool:
        return len(self._history[chat_id]) == 0

    def clear(self, chat_id: int) -> None:
        self._history[chat_id] = []
        self._meta.pop(chat_id, None)

    # ── Meta (for digest) ─────────────────────────────────────

    def touch_user(self, chat_id: int, name: str, username: str) -> None:
        now = datetime.now(timezone.utc).strftime("%d.%m %H:%M")
        if chat_id not in self._meta:
            self._meta[chat_id] = {"name": name, "username": username, "count": 0, "last_at": now}
        self._meta[chat_id]["count"] += 1
        self._meta[chat_id]["last_at"] = now

    def get_recent_dialogs(self) -> list[dict]:
        return list(self._meta.values())

    # ── Supabase persistence ──────────────────────────────────

    def _persist(self, chat_id: int, role: str, content: str) -> None:
        if not self._supabase:
            return
        try:
            self._supabase.table("conversations").insert({
                "chat_id": str(chat_id),
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            log.error("Supabase persist error: %s", e)


store = ConversationStore()
