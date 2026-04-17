"""
Мониторинг публичных Telegram-каналов без User API.
Парсит t.me/s/{channel} — работает для любых открытых каналов.
"""

import re
import logging
import asyncio
import httpx
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# Ключевые слова — вакансии по которым фильтруем
KEYWORDS = [
    "операционный директор", "операционного директора",
    "coo", "chief operating officer", "head of operations",
    "директор по операциям", "руководитель операций",
    "операционный менеджер", "vp operations",
]


class ChannelMonitor:
    def __init__(self) -> None:
        self._channels: list[str] = []
        self._seen_ids: dict[str, set[str]] = {}  # channel -> set of seen msg ids

    # ── Channel management ────────────────────────────────────

    def add_channel(self, username: str) -> bool:
        username = username.lstrip("@").lower().strip()
        if not username:
            return False
        if username not in self._channels:
            self._channels.append(username)
            self._seen_ids[username] = set()
            log.info("Channel added: @%s", username)
        return True

    def remove_channel(self, username: str) -> bool:
        username = username.lstrip("@").lower().strip()
        if username in self._channels:
            self._channels.remove(username)
            self._seen_ids.pop(username, None)
            return True
        return False

    def list_channels(self) -> list[str]:
        return list(self._channels)

    # ── Scanning ──────────────────────────────────────────────

    async def scan_channel(self, username: str) -> list[dict]:
        """Сканирует один публичный канал, возвращает новые релевантные посты."""
        url = f"https://t.me/s/{username}"
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; bot/1.0)"}
                )
            if resp.status_code != 200:
                log.warning("@%s returned HTTP %s", username, resp.status_code)
                return []
            return self._parse(resp.text, username)
        except httpx.TimeoutException:
            log.warning("Timeout scanning @%s", username)
            return []
        except Exception as e:
            log.error("Error scanning @%s: %s", username, e)
            return []

    def _parse(self, html: str, channel: str) -> list[dict]:
        """Парсит HTML, фильтрует по ключевым словам, исключает уже виденные."""
        posts = []
        seen = self._seen_ids.setdefault(channel, set())

        # Извлекаем блоки сообщений с id
        pattern = re.compile(
            r'data-post="[^/]+/(\d+)".*?'
            r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            msg_id, raw_html = match.group(1), match.group(2)
            if msg_id in seen:
                continue
            text = re.sub(r"<[^>]+>", " ", raw_html)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) < 60:
                continue
            text_lower = text.lower()
            if any(kw in text_lower for kw in KEYWORDS):
                seen.add(msg_id)
                posts.append({
                    "channel": channel,
                    "msg_id": msg_id,
                    "text": text[:2000],
                    "url": f"https://t.me/{channel}/{msg_id}",
                    "found_at": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M"),
                })
        return posts

    async def scan_all(self) -> list[dict]:
        """Сканирует все каналы параллельно."""
        if not self._channels:
            return []
        tasks = [self.scan_channel(ch) for ch in self._channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        posts: list[dict] = []
        for r in results:
            if isinstance(r, list):
                posts.extend(r)
        log.info("Scan done: %d new relevant posts", len(posts))
        return posts


monitor = ChannelMonitor()
