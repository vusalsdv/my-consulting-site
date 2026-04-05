"""
Профессиональный профиль владельца.
Хранится в Supabase (таблица owner_profile) + файл как fallback для локальной разработки.
"""

import copy
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)
PROFILE_FILE = Path(__file__).parent / "profile_data.json"

# ── Начальный профиль Вусала ──────────────────────────────────

DEFAULT_PROFILE = {
    "name": "Вусал",
    "target_role": "Операционный директор / COO / Head of Operations",
    "work_format": "удалённо",
    "salary_expectation": "от 300 000 ₽ net",
    "goal": "Войти в 2-3 сильных проекта как COO, развить портфолио кейсов и параллельно строить группу компаний",

    "summary": (
        "Операционный менеджер и COO с 12+ годами опыта. "
        "Строил компании и команды с нуля, выстраивал процессы в условиях высокого роста. "
        "Запускал новые направления в e-commerce, IT, ритейле и стартапах. "
        "Умею работать как Fractional COO — параллельно в нескольких проектах."
    ),

    "experience": [
        {
            "role": "COO",
            "company": "Компания с оборотом 2 млрд ₽",
            "period": "опыт на этой позиции",
            "highlights": [
                "Управление операционной командой",
                "Выстраивание бизнес-процессов при высоком росте",
                "Внедрение OKR и KPI-систем",
                "Найм и онбординг ключевых сотрудников",
            ]
        }
    ],

    "skills": [
        "Построение команд с нуля",
        "Выстраивание и оптимизация бизнес-процессов",
        "Управление P&L",
        "Стратегическое операционное управление",
        "OKR / KPI системы",
        "CustDev и валидация гипотез",
        "Запуск стартапов и новых направлений",
        "Найм и управление людьми",
        "Антикризисное управление",
        "Fractional COO (несколько проектов параллельно)",
    ],

    "industries": ["e-commerce", "IT", "ритейл", "стартапы"],

    "achievements": [
        "Рост выручки клиента с 15 до 48 млн ₽ за 8 месяцев",
        "MVP за 6 недель без постоянного найма (экономия 2 млн ₽)",
        "Запуск онлайн-направления как отдельного юнита без потерь в основном бизнесе",
        "47 успешных консалтинговых проектов",
    ],

    "languages": ["русский (родной)", "английский"],

    "about_consulting": (
        "Параллельно развиваю собственный консалтинг — Fractional COO для предпринимателей. "
        "Ищу работу как наёмный COO чтобы строить портфолио кейсов, "
        "при этом работодателям не знаю о консалтинге."
    ),

    "notes": [],
    "updated_at": "",
}

_SUPABASE_TABLE = "owner_profile"
_SUPABASE_ROW_ID = "main"


def _get_supabase():
    """Возвращает Supabase клиент или None если не настроен."""
    try:
        from .config import SUPABASE_URL, SUPABASE_ANON_KEY
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            return None
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        log.warning("Supabase init error: %s", e)
        return None


class OwnerProfile:
    def __init__(self) -> None:
        self._data: dict = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────

    def _load(self) -> None:
        # 1. Пробуем Supabase
        db = _get_supabase()
        if db:
            try:
                resp = db.table(_SUPABASE_TABLE).select("data").eq("id", _SUPABASE_ROW_ID).execute()
                if resp.data:
                    self._data = resp.data[0]["data"]
                    log.info("Profile loaded from Supabase")
                    return
            except Exception as e:
                log.warning("Supabase profile load error: %s", e)

        # 2. Fallback: файл на диске (локальная разработка)
        if PROFILE_FILE.exists():
            try:
                self._data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
                log.info("Profile loaded from file")
                return
            except Exception as e:
                log.warning("Profile file load error: %s", e)

        # 3. Первый запуск — используем DEFAULT_PROFILE
        self._data = copy.deepcopy(DEFAULT_PROFILE)
        self._save()
        log.info("Profile initialized with defaults")

    def _save(self) -> None:
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # 1. Сохраняем в Supabase
        db = _get_supabase()
        if db:
            try:
                db.table(_SUPABASE_TABLE).upsert({
                    "id": _SUPABASE_ROW_ID,
                    "data": self._data,
                }).execute()
                log.debug("Profile saved to Supabase")
                return
            except Exception as e:
                log.warning("Supabase profile save error: %s", e)

        # 2. Fallback: файл
        try:
            PROFILE_FILE.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            log.error("Profile file save error: %s", e)

    # ── Read ──────────────────────────────────────────────────

    def as_text(self) -> str:
        """Полный профиль в текстовом виде для системного промпта."""
        d = self._data
        skills = "\n".join(f"  - {s}" for s in d.get("skills", []))
        achievements = "\n".join(f"  - {a}" for a in d.get("achievements", []))
        notes = "\n".join(f"  - {n}" for n in d.get("notes", []))

        exp_lines = []
        for e in d.get("experience", []):
            hl = "\n".join(f"    • {h}" for h in e.get("highlights", []))
            exp_lines.append(
                f"  {e.get('role')} @ {e.get('company')} ({e.get('period', '')})\n{hl}"
            )
        experience = "\n".join(exp_lines)

        return f"""=== ПРОФЕССИОНАЛЬНЫЙ ПРОФИЛЬ ВУСАЛА ===

Имя: {d.get('name')}
Целевая позиция: {d.get('target_role')}
Формат работы: {d.get('work_format')}
Ожидания по зарплате: {d.get('salary_expectation')}
Цель: {d.get('goal')}

САММАРИ:
{d.get('summary')}

ОПЫТ:
{experience}

КЛЮЧЕВЫЕ НАВЫКИ:
{skills}

ОТРАСЛИ:
{', '.join(d.get('industries', []))}

ДОСТИЖЕНИЯ:
{achievements}

ЯЗЫКИ: {', '.join(d.get('languages', []))}

КОНТЕКСТ:
{d.get('about_consulting')}

ДОПОЛНИТЕЛЬНЫЕ ЗАМЕТКИ:
{notes if notes else '(нет)'}
"""

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    # ── Write ─────────────────────────────────────────────────

    def add_note(self, note: str) -> None:
        notes = self._data.setdefault("notes", [])
        timestamp = datetime.now(timezone.utc).strftime("%d.%m.%Y")
        notes.append(f"[{timestamp}] {note}")
        if len(notes) > 100:
            self._data["notes"] = notes[-100:]
        self._save()

    def update_field(self, field: str, value) -> None:
        self._data[field] = value
        self._save()

    def add_skill(self, skill: str) -> None:
        skills = self._data.setdefault("skills", [])
        if skill not in skills:
            skills.append(skill)
            self._save()

    def add_achievement(self, achievement: str) -> None:
        self._data.setdefault("achievements", []).append(achievement)
        self._save()

    def add_experience(self, role: str, company: str, period: str, highlights: list[str]) -> None:
        exp = self._data.setdefault("experience", [])
        exp.insert(0, {
            "role": role, "company": company,
            "period": period, "highlights": highlights,
        })
        self._save()

    def show_summary(self) -> str:
        d = self._data
        skills_preview = ", ".join(d.get("skills", [])[:5])
        exp_count = len(d.get("experience", []))
        return (
            f"👤 <b>{d.get('name')}</b>\n"
            f"🎯 {d.get('target_role')}\n"
            f"🖥 {d.get('work_format')} | 💰 {d.get('salary_expectation')}\n\n"
            f"<b>Мест работы:</b> {exp_count}\n"
            f"<b>Навыки:</b> {skills_preview}...\n"
            f"<b>Отрасли:</b> {', '.join(d.get('industries', []))}\n"
            f"<b>Достижений:</b> {len(d.get('achievements', []))}\n"
            f"<b>Заметок:</b> {len(d.get('notes', []))}\n\n"
            f"Обновлён: {d.get('updated_at', '')[:10]}"
        )


profile = OwnerProfile()
