"""
Хранение истории диалогов.
In-memory (всегда) + Supabase (если настроен).
Максимум 20 последних сообщений на диалог — чтобы не раздувать контекст.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone

log = logging.getLogger(__name__)

MAX_HISTORY = 20  # сообщений на диалог


class ConversationStore:
    def __init__(self):
        # chat_id -> list of {"role": "user"/"assistant", "content": "..."}
        self._history: dict[int, list[dict]] = defaultdict(list)
        self._supabase = None
        self._try_init_supabase()

    def _try_init_supabase(self):
        try:
            from .config import SUPABASE_URL, SUPABASE_ANON_KEY
            if SUPABASE_URL and SUPABASE_ANON_KEY:
                from supabase import create_client
                self._supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                log.info("Supabase connected for conversation storage")
        except Exception as e:
            log.warning("Supabase not available: %s", e)

    def get_history(self, chat_id: int) -> list[dict]:
        return list(self._history[chat_id])

    def add_message(self, chat_id: int, role: str, content: str) -> None:
        """Добавляет сообщение в историю, обрезает до MAX_HISTORY."""
        self._history[chat_id].append({"role": role, "content": content})
        # Держим только последние MAX_HISTORY сообщений
        if len(self._history[chat_id]) > MAX_HISTORY:
            self._history[chat_id] = self._history[chat_id][-MAX_HISTORY:]

        # Асинхронно пишем в Supabase (не блокируем)
        self._persist(chat_id, role, content)

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

    def is_new_user(self, chat_id: int) -> bool:
        """True если это первое сообщение от этого chat_id."""
        return len(self._history[chat_id]) == 0

    def clear(self, chat_id: int) -> None:
        self._history[chat_id] = []


# Глобальный инстанс
store = ConversationStore()
