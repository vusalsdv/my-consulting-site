"""
Трекинг вакансий — от находки до результата.
Хранится in-memory; при необходимости расширяется на Supabase.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Status(str, Enum):
    NEW = "🆕 новая"
    APPROVED = "✅ одобрена"
    LETTER_READY = "✍️ письмо готово"
    SENT = "📨 отправлено"
    IN_DIALOG = "💬 диалог"
    INTERVIEW = "🤝 интервью"
    OFFER = "🎯 оффер"
    DECLINED_BY_ME = "🚫 отклонил я"
    REJECTED = "❌ отказ"


@dataclass
class Vacancy:
    vid: str
    company: str
    position: str
    salary: str
    fmt: str          # формат работы
    match: str        # высокое/среднее/низкое
    text: str         # оригинальный текст
    contact: str = ""
    cover_letter: str = ""
    status: Status = Status.NEW
    source: str = ""  # forwarded / channel / manual
    notes: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
    )

    def short_info(self) -> str:
        return (
            f"<b>{self.company}</b> — {self.position}\n"
            f"💰 {self.salary} | 🖥 {self.fmt} | 🎯 соответствие: {self.match}\n"
            f"Статус: {self.status}\n"
            f"ID: <code>{self.vid}</code>"
        )


class Pipeline:
    def __init__(self) -> None:
        self._items: dict[str, Vacancy] = {}
        self._counter = 0

    def add(self, analysis: dict, text: str, source: str = "forwarded") -> Vacancy:
        self._counter += 1
        vid = f"V{self._counter:03d}"
        v = Vacancy(
            vid=vid,
            company=analysis.get("company", "Не указана"),
            position=analysis.get("position", "Не указана"),
            salary=analysis.get("salary", "Не указана"),
            fmt=analysis.get("format", "Не указан"),
            match=analysis.get("match", "среднее"),
            contact=analysis.get("contact", ""),
            text=text,
            source=source,
        )
        self._items[vid] = v
        return v

    def get(self, vid: str) -> Vacancy | None:
        return self._items.get(vid.upper())

    def set_status(self, vid: str, status: Status) -> bool:
        if v := self._items.get(vid.upper()):
            v.status = status
            return True
        return False

    def set_cover(self, vid: str, letter: str) -> None:
        if v := self._items.get(vid.upper()):
            v.cover_letter = letter

    def active(self) -> list[Vacancy]:
        terminal = {Status.DECLINED_BY_ME, Status.REJECTED}
        return [v for v in self._items.values() if v.status not in terminal]

    def summary(self) -> str:
        total = len(self._items)
        if total == 0:
            return "Пайплайн пуст. Перешли мне вакансию или запусти /scan."
        counts: dict[str, int] = {}
        for v in self._items.values():
            counts[v.status] = counts.get(v.status, 0) + 1
        lines = [f"📊 <b>Пайплайн</b> ({total} вакансий):"]
        for status, cnt in counts.items():
            lines.append(f"  {status}: {cnt}")
        return "\n".join(lines)

    def full_list(self) -> str:
        active = self.active()
        if not active:
            return "Активных вакансий нет."
        lines = []
        for v in active:
            lines.append(f"• <code>{v.vid}</code> {v.company} — {v.position} [{v.status}]")
        return "\n".join(lines)


pipeline = Pipeline()
