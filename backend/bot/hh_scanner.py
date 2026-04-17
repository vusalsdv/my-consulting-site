"""
Поиск вакансий на hh.ru через официальный публичный API.
Не требует авторизации для базового поиска.
Документация: https://api.hh.ru/openapi/redoc
"""

import logging
import httpx
from datetime import datetime, timezone

log = logging.getLogger(__name__)

HH_API = "https://api.hh.ru"
HEADERS = {
    "User-Agent": "consulting-job-assistant/1.0 (personal use)",
    "HH-User-Agent": "consulting-job-assistant/1.0 (personal use)",
}

# Поисковые запросы под профиль Вусала
DEFAULT_QUERIES = [
    "операционный директор",
    "COO",
    "head of operations",
    "директор по операциям",
]

# schedule=remote — только удалёнка на hh.ru
SCHEDULE_REMOTE = "remote"

# area=0 — вся Россия
AREA_ALL_RUSSIA = 0


class HHScanner:
    def __init__(self) -> None:
        self._queries: list[str] = list(DEFAULT_QUERIES)
        self._min_salary: int = 300_000   # net RUB
        self._seen_ids: set[str] = set()

    # ── Settings ──────────────────────────────────────────────

    def set_min_salary(self, amount: int) -> None:
        self._min_salary = amount

    def add_query(self, query: str) -> None:
        if query not in self._queries:
            self._queries.append(query)

    # ── Search ────────────────────────────────────────────────

    async def search(self, query: str, per_page: int = 20) -> list[dict]:
        """Ищет вакансии по одному запросу."""
        params = {
            "text": query,
            "area": AREA_ALL_RUSSIA,
            "schedule": SCHEDULE_REMOTE,
            "per_page": per_page,
            "order_by": "publication_time",  # свежие первыми
            "search_field": "name",           # только в названии вакансии
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{HH_API}/vacancies", params=params, headers=HEADERS
                )
            if resp.status_code != 200:
                log.error("HH API error: %s — %s", resp.status_code, resp.text[:200])
                return []
            data = resp.json()
            return data.get("items", [])
        except Exception as e:
            log.error("HH search error for '%s': %s", query, e)
            return []

    async def get_vacancy_detail(self, vacancy_id: str) -> dict | None:
        """Получает полное описание вакансии по ID."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{HH_API}/vacancies/{vacancy_id}", headers=HEADERS
                )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            log.error("HH detail error for %s: %s", vacancy_id, e)
        return None

    async def scan_all(self) -> list[dict]:
        """Ищет по всем запросам, дедуплицирует, фильтрует по зарплате."""
        all_raw: list[dict] = []
        seen_in_run: set[str] = set()

        for query in self._queries:
            items = await self.search(query)
            for item in items:
                vid = item.get("id", "")
                if vid in self._seen_ids or vid in seen_in_run:
                    continue
                seen_in_run.add(vid)
                all_raw.append(item)

        # Фильтруем и форматируем
        results = []
        for item in all_raw:
            formatted = self._format(item)
            if formatted:
                self._seen_ids.add(item["id"])
                results.append(formatted)

        log.info("HH scan: %d new relevant vacancies", len(results))
        return results

    def _format(self, item: dict) -> dict | None:
        """Преобразует raw HH вакансию в наш формат. None = не подходит."""
        # Фильтр по зарплате (если указана)
        salary = item.get("salary")
        if salary:
            salary_from = salary.get("from") or 0
            salary_to = salary.get("to") or salary_from
            currency = salary.get("currency", "RUR")
            is_gross = salary.get("gross", False)

            if currency == "RUR":
                # Если указана gross — примерно net = gross * 0.87
                net_from = int(salary_from * 0.87) if is_gross else salary_from
                if salary_from > 0 and net_from < self._min_salary * 0.7:
                    # Явно ниже порога (с запасом 30% — вдруг указана часть)
                    return None

            salary_str = self._fmt_salary(salary)
        else:
            salary_str = "не указана"

        employer = item.get("employer", {})
        area = item.get("area", {})
        schedule = item.get("schedule", {})

        return {
            "id": item["id"],
            "title": item.get("name", ""),
            "company": employer.get("name", "не указана"),
            "salary": salary_str,
            "city": area.get("name", ""),
            "schedule": schedule.get("name", ""),
            "url": item.get("alternate_url", f"https://hh.ru/vacancy/{item['id']}"),
            "published": item.get("published_at", "")[:10],
            "source": "hh.ru",
            # Текст описания получаем отдельно через get_vacancy_detail
            "snippet": item.get("snippet", {}).get("requirement", "") or "",
        }

    @staticmethod
    def _fmt_salary(s: dict) -> str:
        frm = s.get("from")
        to = s.get("to")
        cur = {"RUR": "₽", "USD": "$", "EUR": "€"}.get(s.get("currency", "RUR"), "₽")
        gross = " (gross)" if s.get("gross") else " (net)"
        if frm and to:
            return f"{frm:,}–{to:,} {cur}{gross}".replace(",", " ")
        elif frm:
            return f"от {frm:,} {cur}{gross}".replace(",", " ")
        elif to:
            return f"до {to:,} {cur}{gross}".replace(",", " ")
        return "по договорённости"


hh_scanner = HHScanner()
