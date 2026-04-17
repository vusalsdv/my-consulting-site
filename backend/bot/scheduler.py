"""
Планировщик автоматических задач.
Запускается как фоновый asyncio-таск при старте бота.
По умолчанию: ежедневное сканирование HH.ru + Telegram-каналов в 9:00 МСК.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from aiogram import Bot

from .config import OWNER_CHAT_ID
from .hh_scanner import hh_scanner
from .channel_monitor import monitor
from .pipeline import pipeline, Status
from .job_scanner import analyze_vacancy

log = logging.getLogger(__name__)

# МСК = UTC+3
MSK_OFFSET = timedelta(hours=3)

# Время автосканирования (час в МСК, 24h формат)
_scan_hour_msk: int = 9
_autoscan_enabled: bool = True


def set_scan_hour(hour: int) -> None:
    global _scan_hour_msk
    _scan_hour_msk = max(0, min(23, hour))


def set_autoscan(enabled: bool) -> None:
    global _autoscan_enabled
    _autoscan_enabled = enabled


def get_status() -> str:
    status = "включено" if _autoscan_enabled else "выключено"
    return f"Автосканирование: {status}, время: {_scan_hour_msk}:00 МСК"


def _seconds_until_next_scan() -> float:
    """Возвращает секунды до следующего запланированного времени сканирования."""
    now_utc = datetime.now(timezone.utc)
    now_msk = now_utc + MSK_OFFSET

    # Следующий запуск сегодня или завтра
    next_run = now_msk.replace(hour=_scan_hour_msk, minute=0, second=0, microsecond=0)
    if next_run <= now_msk:
        next_run += timedelta(days=1)

    delta = next_run - now_msk
    return delta.total_seconds()


async def _run_hh_scan(bot: Bot) -> list[dict]:
    """Запускает HH.ru сканирование и возвращает новые вакансии."""
    try:
        vacancies = await hh_scanner.scan_all()
        return vacancies
    except Exception as e:
        log.error("Auto HH scan error: %s", e)
        return []


async def _run_channel_scan(bot: Bot) -> list[dict]:
    """Запускает сканирование Telegram-каналов."""
    try:
        posts = await monitor.scan_all()
        return posts
    except Exception as e:
        log.error("Auto channel scan error: %s", e)
        return []


async def _send_digest(bot: Bot, hh_vacancies: list[dict], channel_posts: list[dict]) -> None:
    """Отправляет дайджест найденных вакансий владельцу."""
    if not hh_vacancies and not channel_posts:
        return

    lines = [f"🌅 <b>Утренний дайджест вакансий</b>\n"]

    if hh_vacancies:
        lines.append(f"<b>HH.ru — {len(hh_vacancies)} новых вакансий:</b>")
        for v in hh_vacancies[:5]:
            lines.append(
                f"\n• <b>{v['title']}</b> — {v['company']}\n"
                f"  💰 {v['salary']} | 🗓 {v['published']}\n"
                f"  <a href='{v['url']}'>Открыть на HH</a>"
            )
        if len(hh_vacancies) > 5:
            lines.append(f"\n  ...и ещё {len(hh_vacancies) - 5}. Используй /hh чтобы увидеть все.")

    if channel_posts:
        lines.append(f"\n<b>Telegram-каналы — {len(channel_posts)} постов:</b>")
        for p in channel_posts[:3]:
            preview = p.get("text", "")[:150].replace("<", "&lt;").replace(">", "&gt;")
            lines.append(f"\n• @{p.get('channel', '?')}: {preview}...")

    lines.append(f"\n\n/pipeline — активные вакансии | /hh — поиск сейчас")

    text = "\n".join(lines)
    try:
        await bot.send_message(OWNER_CHAT_ID, text, parse_mode="HTML",
                               disable_web_page_preview=True)
    except Exception as e:
        log.error("Digest send error: %s", e)


async def _auto_analyze_top(bot: Bot, vacancies: list[dict]) -> None:
    """Автоматически анализирует топ-3 вакансии и добавляет в pipeline."""
    for v in vacancies[:3]:
        try:
            # Получаем описание если его нет
            text = v.get("snippet", "") or v.get("title", "")
            if not text:
                continue
            analysis = await analyze_vacancy(text)
            match = analysis.get("match", "").lower()
            if match in ("высокое", "среднее"):
                vid = pipeline.add(
                    company=analysis.get("company") or v.get("company", ""),
                    position=analysis.get("position") or v.get("title", ""),
                    salary=analysis.get("salary") or v.get("salary", ""),
                    fmt=analysis.get("format", ""),
                    match=match,
                    text=text,
                    contact=analysis.get("contact", ""),
                )
                log.info("Auto-added to pipeline: %s (%s)", vid, match)
        except Exception as e:
            log.error("Auto-analyze error: %s", e)


async def daily_scan_loop(bot: Bot) -> None:
    """Бесконечный цикл — запускает сканирование раз в сутки в нужное время."""
    log.info("Scheduler started. Next scan at %02d:00 MSK", _scan_hour_msk)

    while True:
        wait = _seconds_until_next_scan()
        log.info("Scheduler: sleeping %.0f seconds until next scan", wait)
        await asyncio.sleep(wait)

        if not _autoscan_enabled:
            log.info("Autoscan disabled — skipping")
            continue

        log.info("Starting daily auto-scan...")
        try:
            hh_vacancies, channel_posts = await asyncio.gather(
                _run_hh_scan(bot),
                _run_channel_scan(bot),
                return_exceptions=True,
            )
            if isinstance(hh_vacancies, Exception):
                hh_vacancies = []
            if isinstance(channel_posts, Exception):
                channel_posts = []

            await _send_digest(bot, hh_vacancies, channel_posts)

            if hh_vacancies:
                await _auto_analyze_top(bot, hh_vacancies)

            log.info("Daily scan done: %d HH, %d TG posts", len(hh_vacancies), len(channel_posts))
        except Exception as e:
            log.error("Daily scan loop error: %s", e)
