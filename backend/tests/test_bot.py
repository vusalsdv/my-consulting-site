"""
Тесты Telegram-бота — без реального Telegram и Claude API.
"""

import os
import pytest

# Фейковые env vars до импорта модулей бота
os.environ.setdefault("TG_BOT_TOKEN", "1234567890:AAFakeTokenForTesting")
os.environ.setdefault("TG_OWNER_CHAT_ID", "999999999")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-fake-key-for-testing")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_ANON_KEY", "")


# ── Storage tests ─────────────────────────────────────────────

def test_storage_empty_on_start():
    from backend.bot.storage import ConversationStore
    s = ConversationStore()
    assert s.get_history(123) == []
    assert s.is_new_user(123) is True


def test_storage_add_message():
    from backend.bot.storage import ConversationStore
    s = ConversationStore()
    s.add_message(1, "user", "Привет")
    s.add_message(1, "assistant", "Здравствуйте!")
    h = s.get_history(1)
    assert len(h) == 2
    assert h[0]["role"] == "user"
    assert h[1]["role"] == "assistant"
    assert s.is_new_user(1) is False


def test_storage_max_history():
    from backend.bot.storage import ConversationStore, MAX_HISTORY
    s = ConversationStore()
    for i in range(MAX_HISTORY + 5):
        s.add_message(1, "user", f"msg {i}")
    assert len(s.get_history(1)) == MAX_HISTORY


def test_storage_clear():
    from backend.bot.storage import ConversationStore
    s = ConversationStore()
    s.add_message(1, "user", "test")
    s.clear(1)
    assert s.is_new_user(1) is True
    assert s.get_history(1) == []


def test_storage_independent_chats():
    from backend.bot.storage import ConversationStore
    s = ConversationStore()
    s.add_message(1, "user", "от первого")
    s.add_message(2, "user", "от второго")
    assert len(s.get_history(1)) == 1
    assert len(s.get_history(2)) == 1


def test_storage_history_is_copy():
    """get_history возвращает копию — нельзя мутировать внутреннее состояние."""
    from backend.bot.storage import ConversationStore
    s = ConversationStore()
    s.add_message(1, "user", "привет")
    h = s.get_history(1)
    h.append({"role": "user", "content": "мутация"})
    assert len(s.get_history(1)) == 1  # не изменилась


# ── AI message builder tests ──────────────────────────────────

def test_build_messages_appends_user():
    from backend.bot.ai import build_messages
    history = [{"role": "assistant", "content": "Здравствуйте!"}]
    result = build_messages(history, "Сколько стоит консультация?")
    assert result[-1] == {"role": "user", "content": "Сколько стоит консультация?"}
    assert len(result) == 2


def test_build_messages_empty_history():
    from backend.bot.ai import build_messages
    result = build_messages([], "Привет")
    assert result == [{"role": "user", "content": "Привет"}]


def test_build_messages_does_not_mutate_history():
    from backend.bot.ai import build_messages
    history = [{"role": "user", "content": "старое"}]
    build_messages(history, "новое")
    assert len(history) == 1  # оригинал не изменился


# ── Config tests ──────────────────────────────────────────────

def test_config_loads():
    from backend.bot import config
    assert config.BOT_TOKEN  # не пустой
    assert config.OWNER_CHAT_ID  # не пустой
    assert config.CLAUDE_MODEL == "claude-sonnet-4-6"
    assert config.ANTHROPIC_API_KEY  # не пустой
