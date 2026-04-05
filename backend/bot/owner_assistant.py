"""
Персональный AI-ассистент для владельца.
Работает как Claude/Claude Code — знает профиль, помнит контекст,
помогает с любыми задачами.
"""

import logging
import anthropic
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OWNER_NAME
from .profile import profile
from .storage import store

log = logging.getLogger(__name__)
_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

OWNER_SYSTEM_PROMPT = """Ты — личный AI-ассистент {owner_name}а. Работаешь как Claude и Claude Code — умный, прямой, эффективный.

{profile_text}

=== КАК ТЫ РАБОТАЕШЬ ===

Ты знаешь всё о профессиональном опыте {owner_name}а и используешь эти знания везде:
- При написании сопроводительных писем — используешь реальный опыт и конкретные достижения
- При анализе вакансий — оцениваешь с точки зрения его реального бэкграунда
- При любом запросе — учитываешь контекст его целей

Ты можешь:
1. Отвечать на любые вопросы и помогать с задачами
2. Обновлять профиль когда {owner_name} рассказывает что-то новое о себе
3. Генерировать тексты, анализировать информацию, строить планы
4. Делегировать задачи специализированным агентам (поиск работы, ресёрч и т.д.)

Принципы:
- Отвечай прямо и по делу, без воды
- Используй конкретику из профиля (реальные цифры, проекты, навыки)
- Если нужно обновить профиль — скажи что добавил новую информацию
- Пиши в том стиле, который удобен {owner_name}у
- Короткие ответы когда уместно, развёрнутые когда нужно

Когда получаешь новую информацию о профессиональном опыте {owner_name}а —
явно скажи: "Запомнил: [кратко что добавил]" чтобы он знал что ты обновил профиль.
"""


async def get_owner_reply(history: list[dict], user_message: str) -> tuple[str, list[str]]:
    """
    Генерирует ответ для владельца.
    Возвращает (текст ответа, список фактов для добавления в профиль).
    """
    system = OWNER_SYSTEM_PROMPT.format(
        owner_name=OWNER_NAME,
        profile_text=profile.as_text(),
    )

    messages = list(history) + [{"role": "user", "content": user_message}]

    response = await _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    )

    if not response.content:
        raise ValueError("Claude вернул пустой ответ")
    reply = response.content[0].text

    # Извлекаем факты для профиля если ассистент явно их отмечает
    new_facts = []
    for line in reply.splitlines():
        if line.startswith("Запомнил:"):
            fact = line[len("Запомнил:"):].strip()
            if fact:
                new_facts.append(fact)

    return reply, new_facts


async def extract_and_save_profile_facts(user_message: str) -> list[str]:
    """
    Анализирует сообщение владельца — извлекает факты о профессиональном опыте.
    Используется когда владелец рассказывает о себе.
    """
    prompt = f"""Проанализируй это сообщение. Если в нём есть новая профессиональная информация
о человеке (опыт, навыки, достижения, проекты, цели) — перечисли факты для сохранения.
Если информации нет — верни пустой список.

Сообщение: {user_message}

Верни ТОЛЬКО список фактов, каждый с новой строки, начиная с "ФАКТ:".
Если нет фактов — верни только слово "НЕТ"."""

    try:
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        if not response.content:
            return []
        text = response.content[0].text.strip()
        if text == "НЕТ" or not text:
            return []
        facts = []
        for line in text.splitlines():
            if line.startswith("ФАКТ:"):
                facts.append(line[5:].strip())
        return facts
    except Exception as e:
        log.error("Profile extraction error: %s", e)
        return []
