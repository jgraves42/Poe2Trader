from __future__ import annotations

from bot.parser import ParsedItem

from .category_map import get_category
from .stats import StatCatalog

MAX_STAT_FILTERS = 8


def _matched_mods(item: ParsedItem, stat_catalog: StatCatalog) -> list[tuple[str, object]]:
    matches: list[tuple[str, object]] = []
    for group, mods in (("implicit", item.implicit_mods), ("explicit", item.explicit_mods)):
        for mod in mods:
            stat_id = stat_catalog.match(mod, group)
            if stat_id is not None:
                matches.append((stat_id, mod))
    return matches


def matched_stat_ids(item: ParsedItem, stat_catalog: StatCatalog) -> set[str]:
    return {stat_id for stat_id, _mod in _matched_mods(item, stat_catalog)}


def build_query(item: ParsedItem, stat_catalog: StatCatalog) -> dict:
    filters: list[dict] = []
    for stat_id, mod in _matched_mods(item, stat_catalog)[:MAX_STAT_FILTERS]:
        filter_entry: dict = {"id": stat_id, "disabled": False}
        if mod.values:
            filter_entry["value"] = {"min": min(mod.values)}
        filters.append(filter_entry)

    query: dict = {
        "query": {
            "status": {"option": "online"},
            "stats": [{"type": "and", "filters": filters}],
        },
        "sort": {"price": "asc"},
    }

    type_filters: dict = {}
    category = get_category(item.item_class)
    if category:
        type_filters["category"] = {"option": category}
    if item.rarity:
        type_filters["rarity"] = {"option": item.rarity.lower()}
    if type_filters:
        query["query"]["filters"] = {"type_filters": {"filters": type_filters}}

    return query
