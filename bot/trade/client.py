from __future__ import annotations

import asyncio
import json
import time
from dataclasses import replace
from urllib.parse import quote

import httpx

from .currency import CHAOS, parse_exchange_rates, to_chaos
from .models import Listing, parse_listing
from .ratelimit import RateLimiter
from .stats import StatCatalog, load_stat_catalog

DEFAULT_USER_AGENT = "poe2-pricer-discord-bot/0.1 (+github.com/search?q=poe2-pricer)"

DEFAULT_SEARCH_RULES = [(5, 10, 60), (15, 60, 300), (30, 300, 1800)]
DEFAULT_FETCH_RULES = [(12, 4, 10), (16, 12, 300)]
DEFAULT_EXCHANGE_RULES = [(5, 15, 60), (10, 90, 300), (30, 300, 1800)]

FETCH_BATCH_SIZE = 10
CACHE_TTL_SECONDS = 300
EXCHANGE_RATE_TTL_SECONDS = 900


class TradeClient:
    def __init__(self, league: str, session_id: str = "", user_agent: str = DEFAULT_USER_AGENT) -> None:
        self.league = league
        cookies = {"POESESSID": session_id} if session_id else {}
        self._client = httpx.AsyncClient(headers={"User-Agent": user_agent}, cookies=cookies, timeout=20.0)
        self._search_limiter = RateLimiter(rules=list(DEFAULT_SEARCH_RULES))
        self._fetch_limiter = RateLimiter(rules=list(DEFAULT_FETCH_RULES))
        self._exchange_limiter = RateLimiter(rules=list(DEFAULT_EXCHANGE_RULES))
        self._search_cache: dict[str, tuple[float, tuple[str, list[str]]]] = {}
        self._rate_cache: dict[str, tuple[float, float]] = {}

    async def __aenter__(self) -> "TradeClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _update_limiter(limiter: RateLimiter, response: httpx.Response) -> None:
        header = response.headers.get("X-Rate-Limit-Ip")
        if header:
            limiter.update_rules_from_header(header)

    async def _throttle(self, limiter: RateLimiter) -> None:
        wait = limiter.wait_time()
        if wait > 0:
            await asyncio.sleep(wait)
        limiter.record_request()

    async def search(self, query: dict) -> tuple[str, list[str]]:
        cache_key = json.dumps(query, sort_keys=True)
        cached = self._search_cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1]

        url = f"https://www.pathofexile.com/api/trade2/search/{quote(self.league)}"

        await self._throttle(self._search_limiter)
        response = await self._client.post(url, json=query)
        self._update_limiter(self._search_limiter, response)

        if response.status_code == 429:
            await asyncio.sleep(float(response.headers.get("Retry-After", 60)))
            response = await self._client.post(url, json=query)
            self._update_limiter(self._search_limiter, response)

        response.raise_for_status()
        data = response.json()
        result = (data["id"], data["result"])
        self._search_cache[cache_key] = (time.monotonic(), result)
        return result

    async def fetch(self, ids: list[str], query_id: str) -> list[dict]:
        entries: list[dict] = []
        for batch_start in range(0, len(ids), FETCH_BATCH_SIZE):
            batch = ids[batch_start : batch_start + FETCH_BATCH_SIZE]
            url = f"https://www.pathofexile.com/api/trade2/fetch/{','.join(batch)}"

            await self._throttle(self._fetch_limiter)
            response = await self._client.get(url, params={"query": query_id})
            self._update_limiter(self._fetch_limiter, response)

            if response.status_code == 429:
                await asyncio.sleep(float(response.headers.get("Retry-After", 60)))
                response = await self._client.get(url, params={"query": query_id})
                self._update_limiter(self._fetch_limiter, response)

            response.raise_for_status()
            data = response.json()
            entries.extend(entry for entry in data.get("result", []) if entry)
        return entries

    async def search_and_fetch(self, query: dict, target_count: int = 30) -> tuple[str, list[Listing]]:
        query_id, ids = await self.search(query)
        raw_entries = await self.fetch(ids[:target_count], query_id)
        listings = [parse_listing(entry) for entry in raw_entries]

        currencies = {listing.price_currency for listing in listings if listing.price_currency}
        rates = await self.get_chaos_rates(list(currencies))
        listings = [
            replace(listing, price_chaos_equivalent=to_chaos(listing.price_amount, listing.price_currency, rates))
            for listing in listings
        ]
        listings.sort(key=lambda listing: (listing.price_chaos_equivalent is None, listing.price_chaos_equivalent))
        return query_id, listings

    async def load_stats(self) -> StatCatalog:
        return await load_stat_catalog(self._client)

    async def get_chaos_rates(self, currencies: list[str]) -> dict[str, float]:
        now = time.monotonic()
        needed = [
            currency
            for currency in set(currencies)
            if currency != CHAOS
            and (currency not in self._rate_cache or now - self._rate_cache[currency][0] >= EXCHANGE_RATE_TTL_SECONDS)
        ]

        if needed:
            url = f"https://www.pathofexile.com/api/trade2/exchange/{quote(self.league)}"
            body = {"query": {"status": {"option": "online"}, "have": needed, "want": [CHAOS]}}

            await self._throttle(self._exchange_limiter)
            response = await self._client.post(url, json=body)
            self._update_limiter(self._exchange_limiter, response)

            if response.status_code == 429:
                await asyncio.sleep(float(response.headers.get("Retry-After", 60)))
                response = await self._client.post(url, json=body)
                self._update_limiter(self._exchange_limiter, response)

            response.raise_for_status()
            fresh_rates = parse_exchange_rates(response.json().get("result") or {})
            for currency, rate in fresh_rates.items():
                self._rate_cache[currency] = (now, rate)

        return {CHAOS: 1.0, **{currency: self._rate_cache[currency][1] for currency in set(currencies) if currency in self._rate_cache}}
