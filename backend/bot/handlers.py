"""
Обработчики входящих сообщений.
- Владелец: полноценный AI-ассистент с памятью профиля + оркестратор
- Клиенты: Claude отвечает как помощник Вусала
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramForbiddenError

from .storage import store
from .config import OWNER_CHAT_ID, OWNER_NAME
from .owner_commands import process_forwarded_vacancy
from .owner_assistant import get_owner_reply, extract_and_save_profile_facts
from .orchestrator import orchestrator
from .profile import profile
from .ai import get_reply

log = logging.getLogger(__name__)
router = Router()

OWNER_HISTORY_KEY = -1  # специальный ключ для истории владельца


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
        store.clear(OWNER_HISTORY_KEY)
        await msg.answer(
            f"Привет, {OWNER_NAME}! Я твой личный ассистент.\n\n"
            f"Я знаю твой профессиональный профиль и помогу с любой задачей:\n"
            f"— Написать письмо под вакансию\n"
            f"— Разобрать задачу и составить план\n"
            f"— Найти вакансии (/hh)\n"
            f"— Просто поговорить и что-то обдумать\n\n"
            f"Рассказывай о себе — буду запоминать и использовать.\n"
            f"/help — все команды | /myprofile — твой профиль"
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


# ── /reset (owner only) ───────────────────────────────────────

@router.message(Command("reset"))
async def cmd_reset(msg: Message) -> None:
    if _is_owner(msg):
        store.clear(OWNER_HISTORY_KEY)
        await msg.answer("История диалога сброшена. Профиль сохранён.")
        return
    store.clear(msg.chat.id)
    await msg.answer("Начнём сначала. Чем могу помочь?")


# ── /myprofile ────────────────────────────────────────────────

@router.message(Command("myprofile"))
async def cmd_myprofile(msg: Message) -> None:
    if not _is_owner(msg):
        return
    await msg.answer(profile.show_summary(), parse_mode="HTML")


# ── /task — явный запрос к оркестратору ──────────────────────

@router.message(Command("task"))
async def cmd_task(msg: Message) -> None:
    if not _is_owner(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer(
            "Использование: <code>/task Найди 5 компаний в e-commerce где нужен COO и подготовь письма</code>",
            parse_mode="HTML",
        )
        return
    task = parts[1]
    await msg.answer(f"🤖 Запускаю агентов...\n\n<i>{task}</i>", parse_mode="HTML")
    await msg.bot.send_chat_action(msg.chat.id, "typing")
    try:
        result = await orchestrator.run(task)
        await msg.answer(result)
    except Exception as e:
        log.error("Orchestrator error: %s", e)
        await msg.answer("Ошибка при выполнении задачи. Попробуй ещё раз.")


# ── Forwarded messages (owner forwards vacancies) ─────────────

@router.message(F.forward_date & F.text)
async def handle_forwarded(msg: Message) -> None:
    if _is_owner(msg):
        await process_forwarded_vacancy(msg)
    else:
        await handle_client_text(msg)


# ── Owner text messages — личный ассистент ────────────────────

@router.message(F.text)
async def handle_text(msg: Message) -> None:
    if _is_owner(msg):
        await handle_owner_text(msg)
    else:
        await handle_client_text(msg)


async def handle_owner_text(msg: Message) -> None:
    """Владелец общается с ботом — полноценный AI-ассистент."""
    user_text = (msg.text or "").strip()
    if not user_text:
        return

    history = store.get_history(OWNER_HISTORY_KEY)
    await msg.bot.send_chat_action(msg.chat.id, "typing")

    try:
        reply, new_facts = await get_owner_reply(history, user_text)
    except Exception as e:
        log.error("Owner assistant error: %s", e)
        await msg.answer("Ошибка. Попробуй ещё раз.")
        return

    # Сохраняем в историю
    store.add_message(OWNER_HISTORY_KEY, "user", user_text)
    store.add_message(OWNER_HISTORY_KEY, "assistant", reply)

    # Сохраняем новые факты в профиль
    if new_facts:
        for fact in new_facts:
            profile.add_note(fact)
        log.info("Added %d facts to profile", len(new_facts))

    # Параллельно пытаемся извлечь профильные факты из сообщения
    try:
        extracted = await extract_and_save_profile_facts(user_text)
        for fact in extracted:
            profile.add_note(fact)
    except Exception:
        pass

    await msg.answer(reply)


async def handle_client_text(msg: Message) -> None:
    """Клиент общается с ботом — отвечает как помощник Вусала."""
    chat_id = msg.chat.id
    user_text = (msg.text or "").strip()
    if not user_text:
        return

    is_new = store.is_new_user(chat_id)
    history = store.get_history(chat_id)

    user = msg.from_user
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Аноним"
    username = f"@{user.username}" if user.username else "нет username"
    store.touch_user(chat_id, name, username)

    await msg.bot.send_chat_action(chat_id, "typing")

    try:
        reply = await get_reply(history, user_text)
    except Exception as e:
        log.error("Claude API error chat %s: %s", chat_id, e)
        await msg.answer("Прошу прощения, произошла техническая ошибка. Попробуйте позже.")
        return

    store.add_message(chat_id, "user", user_text)
    store.add_message(chat_id, "assistant", reply)
    await msg.answer(reply)

    if is_new:
        await _notify_owner(msg.bot, chat_id, msg.from_user, user_text)


# ── Non-text ──────────────────────────────────────────────────

@router.message()
async def handle_other(msg: Message) -> None:
    if _is_owner(msg):
        return
    await msg.answer("Пока работаю только с текстом. Напишите ваш вопрос.")
