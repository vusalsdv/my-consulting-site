"""
Consulting Platform — Backend API
FastAPI + Supabase + Telegram notifications
"""

import os
import logging
from datetime import datetime, timezone

import httpx
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Sentry ───────────────────────────────────────────────────
if sentry_dsn := os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.getenv("ENVIRONMENT", "production"),
        traces_sample_rate=0.2,
    )
    log.info("Sentry initialized")

# ── Rate limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ── App ───────────────────────────────────────────────────────
app = FastAPI(title="Consulting Platform API", version="1.0.0", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────
_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    max_age=600,
)

# ── Supabase (lazy init) ─────────────────────────────────────
_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if url and key:
            from supabase import create_client
            _supabase = create_client(url, key)
    return _supabase


# ── Telegram ─────────────────────────────────────────────────
TG_BOT_TOKEN = os.getenv("TG_NOTIFY_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_NOTIFY_CHAT_ID")


async def _send_tg(text: str) -> None:
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        log.warning("Telegram credentials not set — skipping notification")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "Markdown"})
        if resp.status_code != 200:
            log.error("Telegram error: %s", resp.text)


# ── Schemas ───────────────────────────────────────────────────
class BookingIn(BaseModel):
    name: str
    phone: str
    msg: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Имя слишком короткое")
        if len(v) > 100:
            raise ValueError("Имя слишком длинное")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Укажите телефон или Telegram")
        if len(v) > 100:
            raise ValueError("Контакт слишком длинный")
        return v

    @field_validator("msg")
    @classmethod
    def validate_msg(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError("Сообщение слишком длинное (макс. 2000 символов)")
        return v.strip()


# ── Routes ────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}


@app.post("/api/booking")
@limiter.limit("5/minute")
async def create_booking(request: Request, booking: BookingIn):
    now = datetime.now(timezone.utc).isoformat()

    # 1. Save to Supabase
    db = get_supabase()
    if db:
        try:
            db.table("bookings").insert({
                "name": booking.name,
                "contact": booking.phone,
                "message": booking.msg,
                "status": "new",
                "created_at": now,
            }).execute()
            log.info("Booking saved: %s", booking.name)
        except Exception as exc:
            log.error("Supabase insert error: %s", exc)
            # Don't fail the request — notification still sends
    else:
        log.warning("Supabase not configured — booking not persisted")

    # 2. Telegram notification
    tg_text = (
        "🔔 *Новая заявка с сайта*\n\n"
        f"👤 *Имя:* {booking.name}\n"
        f"📞 *Контакт:* {booking.phone}\n"
        f"💬 *Сообщение:* {booking.msg or '—'}\n\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')} UTC"
    )
    try:
        await _send_tg(tg_text)
    except Exception as exc:
        log.error("Telegram send error: %s", exc)

    return {"success": True, "message": "Заявка принята! Свяжемся в течение 2 часов."}
