"""
Обработчики входящих сообщений.
- Владелец: пересылает вакансии → job scanner
- Клиенты: Claude отвечает как помощник (+ away mode)
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramForbiddenError

from .ai import get_reply
from .storage import store
from .config import OWNER_CHAT_ID, OWNER_NAME, ASSISTANT_NAME
from .owner_commands import process_forwarded_vacancy

log = logging.getLogger(__name__)
router = Router()


def _is_owner(msg: Message) -> bool:
    return str(msg.chat.id) == str(OWNER_CHAT_ID)


async def _notify_owner(bot, chat_id: int, user, first_message: str) -> None:
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Аноним"
    username = f"@{user.username}" if user.username else "нет username"
    text = (
        f"🔔 <b>Новый клиент в боте</b>\n\n"
        f"👤 {name} ({username})\n"
        f"🆔 chat_id: <code>{chat_id}</code>\n\n"
        f"💬 Первое сообщение:\n{first_message}"
    )
    try:
        await bot.send_message(OWNER_CHAT_ID, text, parse_mode="HTML")
    except TelegramForbiddenError:
        log.warning("Cannot notify owner — bot blocked")
    except Exception as e:
        log.error("Owner notification error: %s", e)


# ── /start ────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message) -> None:
    if _is_owner(msg):
        await msg.answer(
            f"Привет! Я твой ассистент.\n\n"
            f"Перешли мне вакансию — разберу и напишу письмо.\n"
            f"Или /help — список всех команд."
        )
        return
    store.clear(msg.chat.id)
    greeting = (
        f"Привет! Я помощник {OWNER_NAME}а.\n\n"
        f"Помогу разобраться с услугами и ответить на вопросы. "
        f"Расскажите, что вас интересует?"
    )
    store.add_message(msg.chat.id, "assistant", greeting)
    await msg.answer(greeting)


# ── /reset ────────────────────────────────────────────────────

@router.message(Command("reset"))
async def cmd_reset(msg: Message) -> None:
    if _is_owner(msg):
        return
    store.clear(msg.chat.id)
    await msg.answer("Начнём сначала. Чем могу помочь?")


# ── Forwarded messages (owner forwards vacancies) ─────────────

@router.message(F.forward_date & F.text)
async def handle_forwarded(msg: Message) -> None:
    if not _is_owner(msg):
        # клиент переслал что-то — обрабатываем как обычный текст
        await handle_text(msg)
        return
    await process_forwarded_vacancy(msg)


# ── Text messages ─────────────────────────────────────────────

@router.message(F.text)
async def handle_text(msg: Message) -> None:
    if _is_owner(msg):
        # Владелец пишет напрямую — не обрабатываем как клиента
        return

    chat_id = msg.chat.id
    user_text = (msg.text or "").strip()
    if not user_text:
        return

    is_new = store.is_new_user(chat_id)
    history = store.get_history(chat_id)

    # Трекаем метаданные для digest
    user = msg.from_user
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Аноним"
    username = f"@{user.username}" if user.username else "нет username"
    store.touch_user(chat_id, name, username)

    await msg.bot.send_chat_action(chat_id, "typing")

    try:
        reply = await get_reply(history, user_text)
    except Exception as e:
        log.error("Claude API error chat %s: %s", chat_id, e)
        await msg.answer(
            "Прошу прощения, произошла техническая ошибка. "
            "Попробуйте позже или свяжитесь напрямую."
        )
        return

    store.add_message(chat_id, "user", user_text)
    store.add_message(chat_id, "assistant", reply)
    await msg.answer(reply)

    # Уведомляем владельца о новом клиенте (если не away — сразу, если away — только первый)
    if is_new:
        await _notify_owner(msg.bot, chat_id, msg.from_user, user_text)


# ── Non-text messages ─────────────────────────────────────────

@router.message()
async def handle_other(msg: Message) -> None:
    if _is_owner(msg):
        return
    await msg.answer(
        "Пока работаю только с текстом. Напишите ваш вопрос."
    )
