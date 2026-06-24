from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

from bot.parser import ParsedMod

STATS_URL = "https://www.pathofexile.com/api/trade2/data/stats"
DEFAULT_CACHE_PATH = Path(".cache/stats.json")
DEFAULT_TTL_SECONDS = 24 * 60 * 60

_NUMBER = re.compile(r"[-+]?\d+\.?\d*")


def _normalize(text: str) -> str:
    return _NUMBER.sub("#", text)


class StatCatalog:
    def __init__(self, index: dict[str, dict[str, str]]) -> None:
        self._index = index

    @classmethod
    def from_raw(cls, raw_groups: list[dict]) -> "StatCatalog":
        index: dict[str, dict[str, str]] = {}
        for group in raw_groups:
            group_index = {
                _normalize(entry["text"]): entry["id"]
                for entry in group.get("entries", [])
            }
            index[group["id"]] = group_index
        return cls(index)

    def match(self, mod: ParsedMod, preferred_group: str) -> str | None:
        normalized = _normalize(mod.text)
        ordered_groups = [preferred_group, *[g for g in self._index if g != preferred_group]]
        for group in ordered_groups:
            group_index = self._index.get(group)
            if group_index and normalized in group_index:
                return group_index[normalized]
        return None


async def load_stat_catalog(
    client: httpx.AsyncClient,
    cache_path: Path = DEFAULT_CACHE_PATH,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> StatCatalog:
    if cache_path.exists():
        cached = json.loads(cache_path.read_text())
        if time.time() - cached["fetched_at"] < ttl_seconds:
            return StatCatalog.from_raw(cached["groups"])

    response = await client.get(STATS_URL)
    response.raise_for_status()
    groups = response.json()["result"]

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({"fetched_at": time.time(), "groups": groups}))

    return StatCatalog.from_raw(groups)
