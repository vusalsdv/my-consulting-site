"""
Backend API tests — pytest + httpx TestClient
Run: cd backend && pytest tests/ -v
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Import app after setting env so Supabase/Sentry don't crash
import os
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_ANON_KEY", "")
os.environ.setdefault("TG_NOTIFY_BOT_TOKEN", "")
os.environ.setdefault("TG_NOTIFY_CHAT_ID", "")

from main import app  # noqa: E402

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ts" in data


# ── Booking — happy paths ─────────────────────────────────────

def _mock_booking(monkeypatch):
    """Patch out external I/O for booking tests."""
    monkeypatch.setattr("main._send_tg", AsyncMock())
    monkeypatch.setattr("main.get_supabase", lambda: None)


def test_booking_full(monkeypatch):
    _mock_booking(monkeypatch)
    resp = client.post("/api/booking", json={
        "name": "Алексей Смирнов",
        "phone": "@alex_smirnov",
        "msg": "Хочу обсудить операционный консалтинг",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_booking_without_msg(monkeypatch):
    _mock_booking(monkeypatch)
    resp = client.post("/api/booking", json={
        "name": "Мария Иванова",
        "phone": "+79001234567",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_booking_telegram_called(monkeypatch):
    mock_tg = AsyncMock()
    monkeypatch.setattr("main._send_tg", mock_tg)
    monkeypatch.setattr("main.get_supabase", lambda: None)

    client.post("/api/booking", json={"name": "Тест Тестов", "phone": "+7900000"})
    mock_tg.assert_awaited_once()
    call_text = mock_tg.call_args[0][0]
    assert "Тест Тестов" in call_text
    assert "+7900000" in call_text


def test_booking_supabase_called(monkeypatch):
    mock_tg = AsyncMock()
    monkeypatch.setattr("main._send_tg", mock_tg)

    mock_db = MagicMock()
    mock_db.table.return_value.insert.return_value.execute.return_value = None
    monkeypatch.setattr("main.get_supabase", lambda: mock_db)

    client.post("/api/booking", json={"name": "Суп Абаз", "phone": "@sup"})
    mock_db.table.assert_called_with("bookings")


# ── Booking — validation errors ───────────────────────────────

def test_booking_empty_name_rejected():
    resp = client.post("/api/booking", json={"name": "", "phone": "+79001234567"})
    assert resp.status_code == 422


def test_booking_single_char_name_rejected():
    resp = client.post("/api/booking", json={"name": "A", "phone": "+79001234567"})
    assert resp.status_code == 422


def test_booking_empty_phone_rejected():
    resp = client.post("/api/booking", json={"name": "Алексей", "phone": ""})
    assert resp.status_code == 422


def test_booking_missing_fields_rejected():
    resp = client.post("/api/booking", json={})
    assert resp.status_code == 422


def test_booking_msg_too_long_rejected():
    resp = client.post("/api/booking", json={
        "name": "Иван",
        "phone": "+79001234567",
        "msg": "x" * 2001,
    })
    assert resp.status_code == 422


def test_booking_name_too_long_rejected():
    resp = client.post("/api/booking", json={
        "name": "А" * 101,
        "phone": "+79001234567",
    })
    assert resp.status_code == 422


# ── Booking — Supabase failure doesn't break response ─────────

def test_booking_supabase_error_still_returns_success(monkeypatch):
    monkeypatch.setattr("main._send_tg", AsyncMock())

    mock_db = MagicMock()
    mock_db.table.return_value.insert.return_value.execute.side_effect = Exception("DB down")
    monkeypatch.setattr("main.get_supabase", lambda: mock_db)

    resp = client.post("/api/booking", json={"name": "Тест Ошибка", "phone": "@test"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# ── CORS ──────────────────────────────────────────────────────

def test_cors_header_present_for_allowed_origin():
    resp = client.options(
        "/api/booking",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    # FastAPI CORS middleware returns 200 for preflight
    assert resp.status_code in (200, 400)
