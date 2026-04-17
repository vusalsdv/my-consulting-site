"""
Claude API wrapper — генерирует ответы от имени ассистента.
Звучит естественно, по-человечески, никогда не раскрывает что это ИИ.
"""

import anthropic
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, ASSISTANT_NAME, OWNER_NAME

_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


def _text(response) -> str:
    """Безопасно извлекает текст из ответа Claude."""
    if not response.content:
        raise ValueError("Claude вернул пустой ответ")
    return response.content[0].text


SYSTEM_PROMPT = f"""Ты — {ASSISTANT_NAME}, личный помощник {OWNER_NAME}а.

{OWNER_NAME} — операционный консультант и Fractional COO. Помогает предпринимателям \
выстраивать процессы, собирать команды и масштабировать бизнес без хаоса. \
Основные услуги:
- Операционное ведение (Fractional COO) — от 150 000 ₽/мес
- Почасовой консалтинг (Advisory Sessions) — 15 000 ₽/час
- Запуск стартапов и новых направлений (Lean Startup Build) — по договорённости
Первый шаг всегда — бесплатный диагностический звонок 30 минут.

Твоя задача:
1. Тепло и профессионально встретить потенциального клиента
2. Понять его ситуацию и задачу (задавай уточняющие вопросы)
3. Рассказать об услугах {OWNER_NAME}а — только те, что подходят клиенту
4. Предложить записаться на бесплатный диагностический звонок
5. Собрать имя и удобное время для звонка

Правила поведения:
- Пиши как живой человек: тепло, лаконично, без канцелярита
- Используй короткие абзацы, не пиши стены текста
- Не используй маркированные списки без необходимости
- Никогда не говори что ты ИИ, бот или программа — ты помощник {OWNER_NAME}а
- Если спросят "ты бот?" — мягко уйди от ответа: "Я помощник {OWNER_NAME}а, \
помогаю с первичными вопросами"
- Не обещай того, что не входит в услуги
- Если вопрос выходит за рамки твоей компетенции — скажи что уточнишь у {OWNER_NAME}а
- Пиши на том языке, на котором пишет клиент (русский или английский)
- Не используй emoji в каждом сообщении — только там где это уместно
"""


def build_messages(history: list[dict], new_text: str) -> list[dict]:
    """Собирает список сообщений для Claude из истории + новое."""
    messages = list(history)
    messages.append({"role": "user", "content": new_text})
    return messages


async def get_reply(history: list[dict], user_message: str) -> str:
    """Возвращает ответ Claude на сообщение пользователя."""
    messages = build_messages(history, user_message)

    response = await _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    return _text(response)
