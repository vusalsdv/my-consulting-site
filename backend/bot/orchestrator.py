"""
Оркестратор агентов.
Получает задачу от владельца → анализирует → делегирует агентам → собирает результат.

Агенты:
  job_search   — поиск вакансий (hh.ru + TG каналы)
  cover_letter — написать сопроводительное письмо
  research     — исследовать компанию / человека / рынок
  analysis     — разобрать документ / вакансию / текст
  draft        — написать любой текст (email, сообщение, пост)
  profile      — обновить профиль
  plan         — составить план действий
"""

import logging
import anthropic
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, OWNER_NAME
from .profile import profile

log = logging.getLogger(__name__)
_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

# ── Agent definitions ─────────────────────────────────────────

AGENTS = {
    "job_search": {
        "name": "Агент поиска работы",
        "description": "Ищет вакансии на hh.ru и в Telegram-каналах по критериям",
        "trigger": ["найди вакансии", "поищи работу", "запусти поиск", "hh", "вакансии"],
    },
    "cover_letter": {
        "name": "Агент сопроводительных писем",
        "description": "Пишет персонализированные письма под конкретную вакансию",
        "trigger": ["напиши письмо", "сопроводительное", "отклик", "письмо рекрутеру"],
    },
    "research": {
        "name": "Агент ресёрча",
        "description": "Исследует компании, людей, рынки, конкурентов",
        "trigger": ["исследуй", "расскажи о компании", "узнай про", "ресёрч", "разведка"],
    },
    "analysis": {
        "name": "Агент анализа",
        "description": "Анализирует тексты, вакансии, документы, ситуации",
        "trigger": ["проанализируй", "разбери", "оцени", "что думаешь о"],
    },
    "draft": {
        "name": "Агент написания текстов",
        "description": "Пишет любые тексты: email, сообщения, посты, описания",
        "trigger": ["напиши", "составь", "подготовь текст", "сформулируй"],
    },
    "plan": {
        "name": "Агент планирования",
        "description": "Строит планы, стратегии, дорожные карты",
        "trigger": ["составь план", "как мне", "стратегия", "что делать", "с чего начать"],
    },
}

ORCHESTRATOR_PROMPT = f"""Ты оркестратор команды AI-агентов {OWNER_NAME}а.

Доступные агенты:
{chr(10).join(f'- {k}: {v["description"]}' for k, v in AGENTS.items())}

Получив задачу, ты должен:
1. Понять что нужно сделать
2. Решить какие агенты нужны и в каком порядке
3. Сформулировать для каждого агента конкретную подзадачу

Верни план в формате:
ПЛАН:
1. [agent_key]: [конкретная задача для этого агента]
2. [agent_key]: [конкретная задача]
...

Если задача простая и не требует делегирования — верни:
ПЛАН:
1. direct: [ответь напрямую]
"""


def _text(response) -> str:
    """Безопасно извлекает текст из ответа Claude."""
    if not response.content:
        raise ValueError("Claude вернул пустой ответ")
    return response.content[0].text


class TaskResult:
    def __init__(self, agent: str, task: str, result: str) -> None:
        self.agent = agent
        self.task = task
        self.result = result


class Orchestrator:

    async def plan(self, task: str) -> list[dict]:
        """Анализирует задачу и возвращает список шагов."""
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            system=ORCHESTRATOR_PROMPT,
            messages=[{"role": "user", "content": f"Задача: {task}"}],
        )
        text = _text(response)
        steps = []
        in_plan = False
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("ПЛАН:"):
                in_plan = True
                continue
            if in_plan and line and line[0].isdigit():
                try:
                    _, rest = line.split(".", 1)
                    agent_key, task_desc = rest.strip().split(":", 1)
                    steps.append({
                        "agent": agent_key.strip(),
                        "task": task_desc.strip(),
                    })
                except ValueError:
                    continue
        return steps

    async def execute_step(self, agent: str, task: str, context: str = "") -> str:
        """Выполняет один шаг — вызывает нужный агент."""
        try:
            if agent == "direct":
                return await self._direct_answer(task, context)
            elif agent == "cover_letter":
                return await self._agent_cover_letter(task)
            elif agent == "research":
                return await self._agent_research(task)
            elif agent == "analysis":
                return await self._agent_analysis(task, context)
            elif agent == "draft":
                return await self._agent_draft(task)
            elif agent == "plan":
                return await self._agent_plan(task)
            elif agent == "job_search":
                return (
                    "Для поиска вакансий используй команды:\n"
                    "/hh — поиск на HH.ru по всем запросам\n"
                    "/scan — сканирование Telegram-каналов\n\n"
                    "Или скажи что именно ищешь и я помогу сформировать запрос."
                )
            else:
                return await self._direct_answer(task, context)
        except Exception as e:
            log.error("Agent %s error for task '%s': %s", agent, task[:50], e)
            return f"[Агент {agent} вернул ошибку: {type(e).__name__}]"

    async def run(self, task: str) -> str:
        """Полный цикл: план → выполнение → сводка."""
        steps = await self.plan(task)
        if not steps:
            return await self._direct_answer(task, "")

        results: list[TaskResult] = []
        for step in steps:
            agent_name = AGENTS.get(step["agent"], {}).get("name", step["agent"])
            result = await self.execute_step(step["agent"], step["task"])
            results.append(TaskResult(agent_name, step["task"], result))

        if len(results) == 1:
            return results[0].result

        # Несколько агентов — собираем сводку
        return await self._consolidate(task, results)

    async def _consolidate(self, original_task: str, results: list[TaskResult]) -> str:
        """Собирает результаты нескольких агентов в единый ответ."""
        parts = [f"Задача: {original_task}\n"]
        for r in results:
            parts.append(f"[{r.agent}]: {r.result}")
        combined = "\n\n".join(parts)

        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=f"Собери результаты работы команды агентов в единый чёткий ответ для {OWNER_NAME}а. Без лишних слов.",
            messages=[{"role": "user", "content": combined}],
        )
        return _text(response)

    # ── Specialized agents ────────────────────────────────────

    async def _direct_answer(self, task: str, context: str) -> str:
        content = f"{task}\n\nКонтекст:\n{context}" if context else task
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=f"Ты личный ассистент {OWNER_NAME}а. Отвечай чётко и по делу.\n\n{profile.as_text()}",
            messages=[{"role": "user", "content": content}],
        )
        return _text(response)

    async def _agent_cover_letter(self, task: str) -> str:
        from .job_scanner import generate_cover_letter
        return await generate_cover_letter(task, {})

    async def _agent_research(self, task: str) -> str:
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=f"Ты агент ресёрча. Собери структурированную информацию по запросу {OWNER_NAME}а.",
            messages=[{"role": "user", "content": task}],
        )
        return _text(response)

    async def _agent_analysis(self, task: str, context: str) -> str:
        full = f"{task}\n\nКонтекст:\n{context}" if context else task
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=f"Ты агент анализа. Дай структурированный разбор.\n\n{profile.as_text()}",
            messages=[{"role": "user", "content": full}],
        )
        return _text(response)

    async def _agent_draft(self, task: str) -> str:
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=f"Ты агент написания текстов. Пишешь от имени или для {OWNER_NAME}а.\n\n{profile.as_text()}",
            messages=[{"role": "user", "content": task}],
        )
        return _text(response)

    async def _agent_plan(self, task: str) -> str:
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            system=f"Ты агент планирования. Строишь конкретные планы с шагами для {OWNER_NAME}а.\n\n{profile.as_text()}",
            messages=[{"role": "user", "content": task}],
        )
        return _text(response)


orchestrator = Orchestrator()
