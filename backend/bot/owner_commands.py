"""
Команды только для владельца (owner).
Управление поиском работы, каналами, пайплайном, режимом away.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command

from .config import OWNER_CHAT_ID
from .pipeline import pipeline, Status
from .channel_monitor import monitor
from .job_scanner import analyze_vacancy, generate_cover_letter
from .storage import store
from .hh_scanner import hh_scanner

log = logging.getLogger(__name__)
owner_router = Router()

# ── Guard ─────────────────────────────────────────────────────

def _is_owner(msg: Message) -> bool:
    return str(msg.chat.id) == str(OWNER_CHAT_ID)


# ── Away mode ─────────────────────────────────────────────────

@owner_router.message(Command("away"))
async def cmd_away(msg: Message) -> None:
    if not _is_owner(msg):
        return
    store.away = True
    await msg.answer(
        "🌙 <b>Режим Away включён.</b>\n\n"
        "Буду самостоятельно отвечать клиентам в боте.\n"
        "Сводку пришлю утром или по команде /digest.\n\n"
        "Для возврата: /back"
    )


@owner_router.message(Command("back"))
async def cmd_back(msg: Message) -> None:
    if not _is_owner(msg):
        return
    store.away = False
    await msg.answer("☀️ Ты онлайн. Буду уведомлять о каждом новом сообщении.")


# ── Pipeline ──────────────────────────────────────────────────

@owner_router.message(Command("pipeline"))
async def cmd_pipeline(msg: Message) -> None:
    if not _is_owner(msg):
        return
    await msg.answer(pipeline.summary(), parse_mode="HTML")


@owner_router.message(Command("list"))
async def cmd_list(msg: Message) -> None:
    if not _is_owner(msg):
        return
    await msg.answer(pipeline.full_list(), parse_mode="HTML")


@owner_router.message(Command("status"))
async def cmd_status(msg: Message) -> None:
    if not _is_owner(msg):
        return
    parts = msg.text.split() if msg.text else []
    if len(parts) < 3:
        await msg.answer(
            "Использование: <code>/status V001 sent</code>\n\n"
            "Статусы: new | approved | sent | dialog | interview | offer | declined | rejected",
            parse_mode="HTML",
        )
        return
    vid, status_str = parts[1], parts[2].lower()
    status_map = {
        "new": Status.NEW, "approved": Status.APPROVED,
        "ready": Status.LETTER_READY, "sent": Status.SENT,
        "dialog": Status.IN_DIALOG, "interview": Status.INTERVIEW,
        "offer": Status.OFFER, "declined": Status.DECLINED_BY_ME,
        "rejected": Status.REJECTED,
    }
    if status_str not in status_map:
        await msg.answer(f"Неизвестный статус: {status_str}")
        return
    if pipeline.set_status(vid, status_map[status_str]):
        v = pipeline.get(vid)
        await msg.answer(f"✅ {vid}: статус обновлён → {v.status}")
    else:
        await msg.answer(f"Вакансия {vid} не найдена.")


# ── Channel monitor ───────────────────────────────────────────

@owner_router.message(Command("addchannel"))
async def cmd_addchannel(msg: Message) -> None:
    if not _is_owner(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) < 2:
        await msg.answer("Использование: <code>/addchannel @hrtech</code>", parse_mode="HTML")
        return
    username = parts[1]
    if monitor.add_channel(username):
        await msg.answer(f"✅ Канал @{username.lstrip('@')} добавлен в мониторинг.")
    else:
        await msg.answer("Не удалось добавить канал.")


@owner_router.message(Command("removechannel"))
async def cmd_removechannel(msg: Message) -> None:
    if not _is_owner(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) < 2:
        await msg.answer("Использование: <code>/removechannel @hrtech</code>", parse_mode="HTML")
        return
    username = parts[1]
    if monitor.remove_channel(username):
        await msg.answer(f"🗑 Канал @{username.lstrip('@')} удалён.")
    else:
        await msg.answer("Канал не найден в списке.")


@owner_router.message(Command("channels"))
async def cmd_channels(msg: Message) -> None:
    if not _is_owner(msg):
        return
    channels = monitor.list_channels()
    if not channels:
        await msg.answer(
            "Каналов нет. Добавь: <code>/addchannel @название</code>", parse_mode="HTML"
        )
        return
    text = "📡 <b>Мониторю каналы:</b>\n" + "\n".join(f"• @{ch}" for ch in channels)
    await msg.answer(text, parse_mode="HTML")


@owner_router.message(Command("scan"))
async def cmd_scan(msg: Message) -> None:
    if not _is_owner(msg):
        return
    channels = monitor.list_channels()
    if not channels:
        await msg.answer(
            "Нет каналов для сканирования. Добавь: <code>/addchannel @название</code>",
            parse_mode="HTML",
        )
        return
    await msg.answer(f"🔍 Сканирую {len(channels)} каналов...")
    posts = await monitor.scan_all()
    if not posts:
        await msg.answer("Новых подходящих вакансий не найдено.")
        return
    await msg.answer(f"Найдено <b>{len(posts)}</b> вакансий. Анализирую...", parse_mode="HTML")
    for post in posts[:10]:  # ограничиваем 10 за раз
        await _process_found_vacancy(msg, post["text"], source=f"@{post['channel']}", url=post.get("url", ""))


# ── Help ──────────────────────────────────────────────────────

@owner_router.message(Command("help"))
async def cmd_help(msg: Message) -> None:
    if not _is_owner(msg):
        return
    await msg.answer(
        "🤖 <b>Команды управления</b>\n\n"
        "<b>Режим присутствия:</b>\n"
        "/away — включить автопилот (бот отвечает клиентам сам)\n"
        "/back — ты онлайн, бот только уведомляет\n"
        "/digest — сводка диалогов за день\n\n"
        "<b>Пайплайн вакансий:</b>\n"
        "/pipeline — сводка по статусам\n"
        "/list — список активных вакансий\n"
        "/status V001 sent — обновить статус\n\n"
        "<b>HH.ru:</b>\n"
        "/hh — поиск по всем запросам\n"
        "/hhsearch [запрос] — быстрый поиск\n"
        "/hhsalary [сумма] — изменить порог ЗП\n\n"
        "<b>Поиск по Telegram-каналам:</b>\n"
        "/addchannel @username — добавить канал\n"
        "/removechannel @username — убрать\n"
        "/channels — список каналов\n"
        "/scan — запустить сканирование\n\n"
        "<b>Вакансии:</b>\n"
        "Просто <b>перешли</b> мне любое сообщение с вакансией — разберу и предложу письмо.\n\n"
        "<b>Личный ассистент:</b>\n"
        "/myprofile — посмотреть сохранённый профиль\n"
        "/task [задача] — запустить агентов на сложную задачу\n"
        "/reset — сбросить историю диалога\n\n"
        "Просто пиши — я помогу с любой задачей и запомню о тебе важное.",
        parse_mode="HTML",
    )


# ── Digest ────────────────────────────────────────────────────

@owner_router.message(Command("digest"))
async def cmd_digest(msg: Message) -> None:
    if not _is_owner(msg):
        return
    dialogs = store.get_recent_dialogs()
    if not dialogs:
        await msg.answer("За последнее время новых диалогов не было.")
        return
    lines = ["📋 <b>Активные диалоги:</b>\n"]
    for d in dialogs:
        lines.append(
            f"👤 {d['name']} ({d['username']})\n"
            f"   Сообщений: {d['count']} | Последнее: {d['last_at']}\n"
        )
    await msg.answer("\n".join(lines), parse_mode="HTML")


# ── Internal: process found/forwarded vacancy ─────────────────

async def _process_found_vacancy(
    msg: Message, text: str, source: str = "forwarded", url: str = ""
) -> None:
    """Анализирует вакансию и показывает владельцу карточку с кнопками."""
    analysis = await analyze_vacancy(text)
    v = pipeline.add(analysis, text, source=source)

    match_emoji = {"высокое": "🟢", "среднее": "🟡", "низкое": "🔴"}.get(
        analysis.get("match", "среднее").lower(), "⚪"
    )

    caption = (
        f"{match_emoji} <b>{v.company}</b> — {v.position}\n"
        f"💰 {v.salary} | 🖥 {v.fmt}\n"
        f"📎 Источник: {source}"
        + (f"\n🔗 {url}" if url else "") +
        f"\n\n<i>{analysis.get('reason', '')}</i>\n\n"
        f"ID: <code>{v.vid}</code>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✍️ Написать письмо", callback_data=f"cover:{v.vid}"),
        InlineKeyboardButton(text="🚫 Пропустить", callback_data=f"skip:{v.vid}"),
    ]])

    await msg.answer(caption, parse_mode="HTML", reply_markup=keyboard)


# ── Callbacks: cover letter & skip ───────────────────────────

@owner_router.callback_query(F.data.startswith("cover:"))
async def cb_cover(cb: CallbackQuery) -> None:
    vid = cb.data.split(":", 1)[1]
    v = pipeline.get(vid)
    if not v:
        await cb.answer("Вакансия не найдена")
        return
    await cb.answer("Генерирую письмо...")
    await cb.message.answer("✍️ Пишу сопроводительное...")
    letter = await generate_cover_letter(v.text, {"raw": "", "company": v.company})
    pipeline.set_cover(vid, letter)
    pipeline.set_status(vid, Status.LETTER_READY)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Отправить", callback_data=f"send:{vid}"),
        InlineKeyboardButton(text="✏️ Переписать", callback_data=f"rewrite:{vid}"),
        InlineKeyboardButton(text="🚫 Отмена", callback_data=f"skip:{vid}"),
    ]])
    await cb.message.answer(
        f"📨 <b>Письмо для {v.company}:</b>\n\n{letter}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@owner_router.callback_query(F.data.startswith("rewrite:"))
async def cb_rewrite(cb: CallbackQuery) -> None:
    vid = cb.data.split(":", 1)[1]
    v = pipeline.get(vid)
    if not v:
        await cb.answer("Вакансия не найдена")
        return
    await cb.answer("Переписываю...")
    letter = await generate_cover_letter(v.text, {"raw": "Сделай версию короче и энергичнее"})
    pipeline.set_cover(vid, letter)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"send:{vid}"),
        InlineKeyboardButton(text="✏️ Ещё раз", callback_data=f"rewrite:{vid}"),
        InlineKeyboardButton(text="🚫 Отмена", callback_data=f"skip:{vid}"),
    ]])
    await cb.message.answer(
        f"📨 <b>Новый вариант:</b>\n\n{letter}", parse_mode="HTML", reply_markup=keyboard
    )


@owner_router.callback_query(F.data.startswith("send:"))
async def cb_send(cb: CallbackQuery) -> None:
    vid = cb.data.split(":", 1)[1]
    v = pipeline.get(vid)
    if not v:
        await cb.answer("Вакансия не найдена")
        return
    pipeline.set_status(vid, Status.SENT)
    await cb.answer("Отмечено как отправлено")
    contact_hint = f"\nКонтакт: {v.contact}" if v.contact and v.contact != "не указан" else ""
    await cb.message.answer(
        f"✅ <b>{vid}</b> отмечена как отправленная.{contact_hint}\n\n"
        f"Скопируй письмо выше и отправь рекрутеру вручную.\n"
        f"Когда начнётся диалог — обнови статус: <code>/status {vid} dialog</code>",
        parse_mode="HTML",
    )


@owner_router.callback_query(F.data.startswith("skip:"))
async def cb_skip(cb: CallbackQuery) -> None:
    vid = cb.data.split(":", 1)[1]
    pipeline.set_status(vid, Status.DECLINED_BY_ME)
    await cb.answer("Пропущено")
    await cb.message.answer(f"🚫 {vid} пропущена.")


# ── HH.ru commands ───────────────────────────────────────────

@owner_router.message(Command("hh"))
async def cmd_hh(msg: Message) -> None:
    if not _is_owner(msg):
        return
    queries = hh_scanner._queries
    await msg.answer(
        f"🔍 <b>Запускаю поиск на hh.ru</b>\n\n"
        f"Запросы: {', '.join(queries)}\n"
        f"Формат: только удалёнка\n"
        f"ЗП: от {hh_scanner._min_salary:,} ₽\n\n"
        f"Ищу...",
        parse_mode="HTML",
    )
    vacancies = await hh_scanner.scan_all()
    if not vacancies:
        await msg.answer("Новых подходящих вакансий на hh.ru не найдено.")
        return
    await msg.answer(f"Найдено <b>{len(vacancies)}</b> вакансий. Анализирую...", parse_mode="HTML")
    for v in vacancies[:8]:  # максимум 8 за раз
        await _send_hh_card(msg, v)


@owner_router.message(Command("hhsearch"))
async def cmd_hhsearch(msg: Message) -> None:
    """Быстрый поиск по конкретному запросу: /hhsearch vp operations"""
    if not _is_owner(msg):
        return
    parts = (msg.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Использование: <code>/hhsearch операционный директор</code>", parse_mode="HTML")
        return
    query = parts[1]
    await msg.answer(f"🔍 Ищу на hh.ru: <i>{query}</i>...", parse_mode="HTML")
    items = await hh_scanner.search(query, per_page=10)
    if not items:
        await msg.answer("Ничего не найдено.")
        return
    formatted = [hh_scanner._format(i) for i in items if hh_scanner._format(i)]
    await msg.answer(f"Найдено <b>{len(formatted)}</b> результатов:", parse_mode="HTML")
    for v in formatted[:5]:
        await _send_hh_card(msg, v)


@owner_router.message(Command("hhsalary"))
async def cmd_hhsalary(msg: Message) -> None:
    """Изменить минимальную зарплату: /hhsalary 350000"""
    if not _is_owner(msg):
        return
    parts = (msg.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer(
            f"Текущий порог: <b>{hh_scanner._min_salary:,} ₽</b>\n"
            f"Изменить: <code>/hhsalary 350000</code>",
            parse_mode="HTML",
        )
        return
    hh_scanner.set_min_salary(int(parts[1]))
    await msg.answer(f"✅ Минимальная зарплата: <b>{hh_scanner._min_salary:,} ₽</b>", parse_mode="HTML")


async def _send_hh_card(msg: Message, v: dict) -> None:
    """Отправляет карточку вакансии с HH с кнопками."""
    text = (
        f"🏢 <b>{v['company']}</b>\n"
        f"📌 {v['title']}\n"
        f"💰 {v['salary']}\n"
        f"🖥 {v['schedule']} | 📍 {v['city']}\n"
        f"📅 {v['published']}\n"
        f"🔗 <a href='{v['url']}'>Открыть на hh.ru</a>"
        + (f"\n\n<i>{v['snippet'][:200]}</i>" if v.get("snippet") else "")
    )
    # Сохраняем в pipeline как предварительную вакансию
    analysis = {
        "company": v["company"],
        "position": v["title"],
        "salary": v["salary"],
        "format": v["schedule"],
        "match": "среднее",
        "reason": "Найдена на hh.ru",
        "contact": v["url"],
        "raw": f"Компания: {v['company']}\nДолжность: {v['title']}\nЗП: {v['salary']}",
    }
    vac = pipeline.add(analysis, v.get("snippet", v["title"]), source="hh.ru")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✍️ Написать письмо", callback_data=f"cover:{vac.vid}"),
        InlineKeyboardButton(text="🚫 Пропустить", callback_data=f"skip:{vac.vid}"),
    ]])
    await msg.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)


# ── Export for use in handlers.py ────────────────────────────

async def process_forwarded_vacancy(msg: Message) -> None:
    """Вызывается из handlers.py когда владелец пересылает вакансию."""
    text = msg.text or msg.caption or ""
    # Добавляем оригинальный текст пересланного сообщения если есть
    if msg.forward_from_chat:
        source = f"@{msg.forward_from_chat.username or msg.forward_from_chat.title}"
    elif msg.forward_sender_name:
        source = msg.forward_sender_name
    else:
        source = "переслано"
    await msg.answer("🔍 Анализирую вакансию...")
    await _process_found_vacancy(msg, text, source=source)
