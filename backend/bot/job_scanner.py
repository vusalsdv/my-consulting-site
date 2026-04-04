"""
Анализирует вакансии и генерирует сопроводительные письма.
Работает с пересланными сообщениями от владельца.
"""

import logging
import anthropic
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL

log = logging.getLogger(__name__)
_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Профиль соискателя — редактируй под себя
JOB_SEEKER_PROFILE = """
Имя: Вусал
Позиция: Операционный директор / COO / Head of Operations
Формат: только удалённо (или гибрид с редкими выездами)
Зарплата: от 300 000 ₽ net
Цель: войти в 2-3 сильных проекта, развить портфолио реальных кейсов

Опыт и компетенции:
- 12+ лет в операционном управлении
- Строил команды с нуля, выстраивал бизнес-процессы в условиях роста
- Запускал новые направления в e-commerce, IT, ритейле, стартапах
- Управление P&L, внедрение OKR и KPI-систем
- Опыт работы COO в компании с оборотом 2 млрд ₽
- Fractional COO — умеет работать параллельно в нескольких проектах
"""

_ANALYZE_PROMPT = """Проанализируй вакансию и верни структурированный ответ.

Профиль соискателя:
{profile}

Критерии соответствия:
- Позиция: COO / операционный директор / head of operations / директор по операциям
- Формат: удалённо или гибрид
- Зарплата: от 300 000 ₽ net (если указана)

Текст вакансии:
{text}

Верни ответ строго в этом формате:
КОМПАНИЯ: [название или "не указана"]
ДОЛЖНОСТЬ: [должность]
ЗАРПЛАТА: [зарплата или "не указана"]
ФОРМАТ: [удалённо / гибрид / офис / не указан]
СООТВЕТСТВИЕ: [высокое / среднее / низкое]
ПРИЧИНА: [1-2 предложения]
КОНТАКТ: [ссылка, @username или "не указан"]
"""

_COVER_LETTER_PROMPT = """Напиши сопроводительное письмо в Telegram рекрутеру — коротко и живо.

Профиль соискателя:
{profile}

Вакансия:
{vacancy_text}

Анализ вакансии:
{analysis}

Требования:
- Пиши от первого лица, как будто Вусал пишет сам
- 3-4 абзаца, без воды
- Покажи что читал вакансию — упомяни конкретику из неё
- Живой язык, не шаблонный HR-стиль
- Не раскрывай что это написал ИИ
- В конце — конкретный следующий шаг (предложи коротко созвониться)
- Только текст письма, без темы и заголовков
"""


async def analyze_vacancy(text: str) -> dict:
    """Анализирует текст вакансии, возвращает структурированные данные."""
    prompt = _ANALYZE_PROMPT.format(profile=JOB_SEEKER_PROFILE, text=text)
    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    result: dict = {"raw": raw, "text": text}
    for line in raw.splitlines():
        for key, field in [
            ("КОМПАНИЯ:", "company"), ("ДОЛЖНОСТЬ:", "position"),
            ("ЗАРПЛАТА:", "salary"), ("ФОРМАТ:", "format"),
            ("СООТВЕТСТВИЕ:", "match"), ("ПРИЧИНА:", "reason"),
            ("КОНТАКТ:", "contact"),
        ]:
            if line.startswith(key):
                result[field] = line[len(key):].strip()
    return result


async def generate_cover_letter(vacancy_text: str, analysis: dict) -> str:
    """Генерирует сопроводительное письмо под конкретную вакансию."""
    prompt = _COVER_LETTER_PROMPT.format(
        profile=JOB_SEEKER_PROFILE,
        vacancy_text=vacancy_text,
        analysis=analysis.get("raw", ""),
    )
    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=900,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
