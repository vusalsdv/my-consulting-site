"""
Обработчики сообщений Telegram-бота.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramForbiddenError

from .ai import get_reply
from .storage import store
from .config import OWNER_CHAT_ID, OWNER_NAME, ASSISTANT_NAME

log = logging.getLogger(__name__)
router = Router()


async def _notify_owner(bot, chat_id: int, user, first_message: str) -> None:
    """Уведомляет владельца о новом клиенте."""
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Аноним"
    username = f"@{user.username}" if user.username else "нет username"
    text = (
        f"🔔 Новый клиент в боте\n\n"
        f"👤 {name} ({username})\n"
        f"🆔 chat_id: {chat_id}\n\n"
        f"💬 Первое сообщение:\n{first_message}"
    )
    try:
        await bot.send_message(OWNER_CHAT_ID, text)
    except TelegramForbiddenError:
        log.warning("Cannot notify owner — bot is blocked by owner")
    except Exception as e:
        log.error("Owner notification error: %s", e)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Приветствие при /start."""
    store.clear(message.chat.id)
    greeting = (
        f"Привет! Я помощник {OWNER_NAME}а.\n\n"
        f"Помогу разобраться с услугами и ответить на вопросы. "
        f"Расскажите, что вас интересует?"
    )
    store.add_message(message.chat.id, "assistant", greeting)
    await message.answer(greeting)


@router.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    """Сброс истории диалога."""
    store.clear(message.chat.id)
    await message.answer("Начнём сначала. Чем могу помочь?")


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Основной обработчик текстовых сообщений."""
    chat_id = message.chat.id
    user_text = message.text.strip()

    if not user_text:
        return

    is_new = store.is_new_user(chat_id)
    history = store.get_history(chat_id)

    # Показываем "печатает..."
    await message.bot.send_chat_action(chat_id, "typing")

    try:
        reply = await get_reply(history, user_text)
    except Exception as e:
        log.error("Claude API error for chat %s: %s", chat_id, e)
        await message.answer(
            "Прошу прощения, произошла техническая ошибка. "
            "Попробуйте написать чуть позже или свяжитесь напрямую."
        )
        return

    # Сохраняем в историю
    store.add_message(chat_id, "user", user_text)
    store.add_message(chat_id, "assistant", reply)

    await message.answer(reply)

    # Уведомляем владельца о новом клиенте
    if is_new:
        await _notify_owner(message.bot, chat_id, message.from_user, user_text)


@router.message()
async def handle_other(message: Message) -> None:
    """Нетекстовые сообщения (фото, стикеры и т.д.)."""
    await message.answer(
        "Пока я работаю только с текстовыми сообщениями. "
        "Напишите ваш вопрос текстом."
    )
