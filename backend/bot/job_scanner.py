"""
Анализирует вакансии и генерирует сопроводительные письма.
Работает с пересланными сообщениями от владельца.
"""

import logging
import anthropic
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from .profile import profile

log = logging.getLogger(__name__)
_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_ANALYZE_PROMPT = """Проанализируй вакансию и верни структурированный ответ.

Профиль соискателя:
{profile}

Критерии соответствия:
- Позиция: {target_role}
- Формат: {work_format}
- Зарплата: {salary} (если указана)

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

Полный профиль соискателя (используй ТОЛЬКО релевантный опыт под эту вакансию):
{profile}

Вакансия:
{vacancy_text}

Анализ вакансии:
{analysis}

Требования:
- Пиши от первого лица, как будто {name} пишет сам
- 3-4 абзаца, без воды
- Выбери из профиля 2-3 самых релевантных кейса/достижения под ЭТУ вакансию
- Покажи что читал вакансию — упомяни конкретику из неё
- Живой язык, не шаблонный HR-стиль
- Не раскрывай что это написал ИИ
- В конце — конкретный следующий шаг (предложи коротко созвониться)
- Только текст письма, без темы и заголовков
"""


async def analyze_vacancy(text: str) -> dict:
    """Анализирует текст вакансии, возвращает структурированные данные."""
    prompt = _ANALYZE_PROMPT.format(
        profile=profile.as_text(),
        target_role=profile.get("target_role", "COO / операционный директор"),
        work_format=profile.get("work_format", "удалённо"),
        salary=profile.get("salary_expectation", "от 300 000 ₽ net"),
        text=text,
    )
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
        profile=profile.as_text(),
        name=profile.get("name", "Вусал"),
        vacancy_text=vacancy_text,
        analysis=analysis.get("raw", ""),
    )
    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
