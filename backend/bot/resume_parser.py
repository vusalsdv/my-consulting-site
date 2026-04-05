"""
Парсер резюме.
Владелец пересылает файл (PDF, DOCX, TXT) — бот извлекает текст,
структурирует через Claude и сохраняет в профиль.
"""

import io
import json
import logging
import tempfile
from pathlib import Path

import anthropic
from aiogram.types import Message, Document

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from .profile import profile

log = logging.getLogger(__name__)
_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SUPPORTED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}

SUPPORTED_EXT = {".pdf", ".docx", ".doc", ".txt"}

_PARSE_PROMPT = """Ты парсишь резюме. Извлеки структурированную информацию и верни строго валидный JSON.

Резюме:
{text}

Верни JSON в точно таком формате (все поля обязательны, пустые — пустые строки/списки):
{{
  "name": "имя",
  "summary": "краткое саммари кандидата 2-3 предложения",
  "target_role": "целевая должность",
  "work_format": "формат работы (удалённо/гибрид/офис)",
  "salary_expectation": "ожидания по зарплате",
  "experience": [
    {{
      "role": "должность",
      "company": "компания",
      "period": "период (напр. 2020–2023)",
      "highlights": ["ключевое достижение 1", "ключевое достижение 2"]
    }}
  ],
  "skills": ["навык1", "навык2"],
  "achievements": ["достижение 1", "достижение 2"],
  "industries": ["отрасль1", "отрасль2"],
  "languages": ["язык1", "язык2"]
}}

Правила:
- Только JSON, без пояснений до и после
- highlights — конкретные достижения с цифрами если есть
- achievements — самые яркие результаты из всего резюме
- Сохраняй оригинальные формулировки, не переписывай"""


async def extract_text(doc: Document, bot) -> str:
    """Скачивает файл и извлекает из него текст."""
    file = await bot.get_file(doc.file_id)

    buf = io.BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    buf.seek(0)

    ext = Path(doc.file_name or "").suffix.lower()
    mime = doc.mime_type or ""

    # PDF
    if ext == ".pdf" or "pdf" in mime:
        return _read_pdf(buf)

    # DOCX
    if ext in (".docx", ".doc") or "word" in mime or "officedocument" in mime:
        return _read_docx(buf)

    # TXT и всё остальное — как текст
    return buf.read().decode("utf-8", errors="replace")


def _read_pdf(buf: io.BytesIO) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(buf) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def _read_docx(buf: io.BytesIO) -> str:
    from docx import Document as DocxDocument
    doc = DocxDocument(buf)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


async def parse_resume(text: str) -> dict:
    """Вызывает Claude для структурированного извлечения данных из резюме."""
    prompt = _PARSE_PROMPT.format(text=text[:8000])
    response = await _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    if not response.content:
        raise ValueError("Пустой ответ от Claude")
    raw = response.content[0].text.strip()

    # Убираем возможные ```json ... ``` обёртки
    if "```" in raw:
        parts = raw.split("```")
        # берём первый блок внутри тройных кавычек
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


async def save_resume_to_profile(parsed: dict) -> dict[str, int]:
    """
    Сохраняет данные из резюме в профиль.
    Возвращает статистику: сколько чего добавлено.
    """
    stats = {"experience": 0, "skills": 0, "achievements": 0}

    # Обновляем базовые поля если они пришли непустые
    for field in ("name", "summary", "target_role", "work_format",
                  "salary_expectation", "languages"):
        val = parsed.get(field)
        if val and (isinstance(val, str) and val.strip() or isinstance(val, list) and val):
            profile.update_field(field, val)

    # Отрасли
    for ind in parsed.get("industries", []):
        existing = profile.get("industries", [])
        if ind and ind not in existing:
            profile.update_field("industries", existing + [ind])

    # Опыт — проверяем дубликаты по связке роль+компания
    existing_exp = profile.get("experience", [])
    existing_keys = {
        (e.get("role", "").lower(), e.get("company", "").lower())
        for e in existing_exp
    }
    new_exp = []
    for exp in parsed.get("experience", []):
        key = (exp.get("role", "").lower(), exp.get("company", "").lower())
        if key not in existing_keys and exp.get("role") and exp.get("company"):
            new_exp.append(exp)
            existing_keys.add(key)
            stats["experience"] += 1
    if new_exp:
        profile.update_field("experience", new_exp + existing_exp)

    # Навыки — add_skill уже дедуплицирует
    for skill in parsed.get("skills", []):
        if skill:
            before = len(profile.get("skills", []))
            profile.add_skill(skill)
            if len(profile.get("skills", [])) > before:
                stats["skills"] += 1

    # Достижения — дедупликация по нечёткому совпадению (первые 40 символов)
    existing_ach = {a[:40].lower() for a in profile.get("achievements", [])}
    for ach in parsed.get("achievements", []):
        if ach and ach[:40].lower() not in existing_ach:
            profile.add_achievement(ach)
            existing_ach.add(ach[:40].lower())
            stats["achievements"] += 1

    return stats


def is_supported(doc: Document) -> bool:
    """Проверяет что файл поддерживается."""
    ext = Path(doc.file_name or "").suffix.lower()
    mime = doc.mime_type or ""
    return ext in SUPPORTED_EXT or any(m in mime for m in ("pdf", "word", "text"))
