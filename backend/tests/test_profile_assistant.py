"""
Тесты profile.py, owner_assistant.py, orchestrator.py — без реального API.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Фейковые env vars до импорта модулей
os.environ.setdefault("TG_BOT_TOKEN", "1234567890:AAFakeTokenForTesting")
os.environ.setdefault("TG_OWNER_CHAT_ID", "999999999")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-fake-key-for-testing")
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_ANON_KEY", "")


# ── Profile tests ─────────────────────────────────────────────

def _make_profile(tmp_path):
    """Создаёт экземпляр OwnerProfile с временным файлом."""
    from backend.bot.profile import OwnerProfile, DEFAULT_PROFILE
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
    return p, profile_file


def test_profile_loads_default(tmp_path):
    from backend.bot.profile import OwnerProfile, DEFAULT_PROFILE
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
    assert p.get("name") == DEFAULT_PROFILE["name"]
    assert p.get("target_role") == DEFAULT_PROFILE["target_role"]


def test_profile_persists_to_disk(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
        p.add_note("Тестовая заметка")
    assert profile_file.exists()
    data = json.loads(profile_file.read_text(encoding="utf-8"))
    notes = data.get("notes", [])
    assert any("Тестовая заметка" in n for n in notes)


def test_profile_add_note(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
        p.add_note("Заметка 1")
        p.add_note("Заметка 2")
    notes = p.get("notes", [])
    assert len(notes) == 2
    assert any("Заметка 1" in n for n in notes)
    assert any("Заметка 2" in n for n in notes)


def test_profile_add_skill(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
        initial_count = len(p.get("skills", []))
        p.add_skill("Новый навык")
    skills = p.get("skills", [])
    assert len(skills) == initial_count + 1
    assert "Новый навык" in skills


def test_profile_add_skill_no_duplicates(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
        existing = p.get("skills", [])[0]
        count_before = len(p.get("skills", []))
        p.add_skill(existing)  # добавляем дубликат
    assert len(p.get("skills", [])) == count_before


def test_profile_as_text_contains_name(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
    text = p.as_text()
    assert "Вусал" in text
    assert "COO" in text


def test_profile_show_summary(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
    summary = p.show_summary()
    assert "Вусал" in summary
    assert "Навыки" in summary


def test_profile_add_achievement(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
        initial = len(p.get("achievements", []))
        p.add_achievement("Новое достижение XYZ")
    assert len(p.get("achievements", [])) == initial + 1
    assert "Новое достижение XYZ" in p.get("achievements", [])


def test_profile_notes_capped_at_100(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
        for i in range(110):
            p.add_note(f"Заметка {i}")
    assert len(p.get("notes", [])) <= 100


def test_profile_loads_from_existing_file(tmp_path):
    from backend.bot.profile import OwnerProfile
    profile_file = tmp_path / "profile_data.json"
    data = {"name": "Тест", "notes": ["существующая заметка"], "skills": [], "achievements": [],
            "experience": [], "target_role": "CTO", "work_format": "remote",
            "salary_expectation": "500k", "goal": "", "summary": "", "industries": [],
            "languages": [], "about_consulting": ""}
    profile_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with patch("backend.bot.profile.PROFILE_FILE", profile_file):
        p = OwnerProfile()
    assert p.get("name") == "Тест"
    assert p.get("notes") == ["существующая заметка"]


# ── Owner assistant tests ─────────────────────────────────────

def _mock_anthropic_response(text: str):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=text)]
    return mock_resp


def _async_mock_create(text: str):
    """Возвращает AsyncMock который отдаёт нужный ответ."""
    mock = AsyncMock(return_value=_mock_anthropic_response(text))
    return mock


@pytest.mark.asyncio
async def test_get_owner_reply_returns_tuple():
    from backend.bot.owner_assistant import get_owner_reply
    with patch("backend.bot.owner_assistant._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response("Привет! Чем могу помочь?")
        )
        reply, facts = await get_owner_reply([], "Привет")
    assert isinstance(reply, str)
    assert isinstance(facts, list)
    assert reply == "Привет! Чем могу помочь?"
    assert facts == []


@pytest.mark.asyncio
async def test_get_owner_reply_extracts_facts():
    from backend.bot.owner_assistant import get_owner_reply
    reply_text = "Запомнил: Работал в компании ABC как COO\nОтлично, учту это."
    with patch("backend.bot.owner_assistant._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(reply_text)
        )
        reply, facts = await get_owner_reply([], "Работал в компании ABC")
    assert len(facts) == 1
    assert "Работал в компании ABC как COO" in facts[0]


@pytest.mark.asyncio
async def test_extract_and_save_profile_facts_no_facts():
    from backend.bot.owner_assistant import extract_and_save_profile_facts
    with patch("backend.bot.owner_assistant._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response("НЕТ")
        )
        facts = await extract_and_save_profile_facts("Погода хорошая")
    assert facts == []


@pytest.mark.asyncio
async def test_extract_and_save_profile_facts_with_facts():
    from backend.bot.owner_assistant import extract_and_save_profile_facts
    with patch("backend.bot.owner_assistant._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response("ФАКТ: Знает Python\nФАКТ: Опыт в стартапах 5 лет")
        )
        facts = await extract_and_save_profile_facts("Знаю Python, работал в стартапах")
    assert len(facts) == 2
    assert "Знает Python" in facts[0]


@pytest.mark.asyncio
async def test_extract_handles_api_error():
    from backend.bot.owner_assistant import extract_and_save_profile_facts
    with patch("backend.bot.owner_assistant._client") as mock_client:
        mock_client.messages.create = AsyncMock(side_effect=Exception("API Error"))
        facts = await extract_and_save_profile_facts("Любое сообщение")
    assert facts == []


# ── Orchestrator tests ────────────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_plan_parses_steps():
    from backend.bot.orchestrator import Orchestrator
    plan_text = "ПЛАН:\n1. draft: Написать email\n2. plan: Составить стратегию"
    with patch("backend.bot.orchestrator._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response(plan_text)
        )
        o = Orchestrator()
        steps = await o.plan("Помоги с письмом")
    assert len(steps) == 2
    assert steps[0]["agent"] == "draft"
    assert "email" in steps[0]["task"].lower()
    assert steps[1]["agent"] == "plan"


@pytest.mark.asyncio
async def test_orchestrator_plan_returns_empty_on_no_plan():
    from backend.bot.orchestrator import Orchestrator
    with patch("backend.bot.orchestrator._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response("Конечно помогу!")
        )
        o = Orchestrator()
        steps = await o.plan("Привет")
    assert steps == []


@pytest.mark.asyncio
async def test_orchestrator_execute_direct():
    from backend.bot.orchestrator import Orchestrator
    with patch("backend.bot.orchestrator._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response("Прямой ответ")
        )
        o = Orchestrator()
        result = await o.execute_step("direct", "Расскажи о себе")
    assert result == "Прямой ответ"


@pytest.mark.asyncio
async def test_orchestrator_execute_unknown_agent_falls_back():
    from backend.bot.orchestrator import Orchestrator
    with patch("backend.bot.orchestrator._client") as mock_client:
        mock_client.messages.create = AsyncMock(
            return_value=_mock_anthropic_response("Ответ запасного агента")
        )
        o = Orchestrator()
        result = await o.execute_step("unknown_agent", "Задача")
    assert result == "Ответ запасного агента"


@pytest.mark.asyncio
async def test_orchestrator_execute_job_search_returns_hint():
    from backend.bot.orchestrator import Orchestrator
    o = Orchestrator()
    result = await o.execute_step("job_search", "Найди вакансии COO")
    assert "/hh" in result or "/scan" in result


@pytest.mark.asyncio
async def test_orchestrator_run_single_step():
    from backend.bot.orchestrator import Orchestrator
    plan_text = "ПЛАН:\n1. direct: Ответь на вопрос"
    answer_text = "Вот ответ на ваш вопрос"
    responses = [_mock_anthropic_response(plan_text), _mock_anthropic_response(answer_text)]
    call_count = 0

    async def mock_create(**kwargs):
        nonlocal call_count
        r = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return r

    with patch("backend.bot.orchestrator._client") as mock_client:
        mock_client.messages.create = mock_create
        o = Orchestrator()
        result = await o.run("Простой вопрос")
    assert result == answer_text


@pytest.mark.asyncio
async def test_orchestrator_run_empty_plan_falls_back():
    from backend.bot.orchestrator import Orchestrator
    responses = [
        _mock_anthropic_response("Нет плана"),
        _mock_anthropic_response("Прямой ответ"),
    ]
    call_count = 0

    async def mock_create(**kwargs):
        nonlocal call_count
        r = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return r

    with patch("backend.bot.orchestrator._client") as mock_client:
        mock_client.messages.create = mock_create
        o = Orchestrator()
        result = await o.run("Какой-то вопрос")
    assert result == "Прямой ответ"
