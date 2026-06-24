from pathlib import Path

from bot.parser import parse_item
from bot.parser.models import ParsedItem, ParsedMod
from bot.trade.query import MAX_STAT_FILTERS, build_query, matched_stat_ids
from bot.trade.stats import StatCatalog

SAMPLES_DIR = Path(__file__).parent / "samples"


def test_build_query_includes_category_stats_and_rarity():
    item = parse_item((SAMPLES_DIR / "rare_boots.txt").read_text())
    catalog = StatCatalog.from_raw(
        [
            {
                "id": "explicit",
                "entries": [
                    {"id": "explicit.stat_movespeed", "text": "#% increased Movement Speed", "type": "explicit"},
                    {"id": "explicit.stat_life", "text": "# to maximum Life", "type": "explicit"},
                ],
            }
        ]
    )

    query = build_query(item, catalog)

    assert query["query"]["status"] == {"option": "online"}
    assert query["sort"] == {"price": "asc"}

    type_filters = query["query"]["filters"]["type_filters"]["filters"]
    assert type_filters["category"] == {"option": "armour.boots"}
    assert type_filters["rarity"] == {"option": "rare"}

    filters = query["query"]["stats"][0]["filters"]
    filter_ids = {f["id"] for f in filters}
    assert {"explicit.stat_movespeed", "explicit.stat_life"} <= filter_ids

    move_speed_filter = next(f for f in filters if f["id"] == "explicit.stat_movespeed")
    assert move_speed_filter["value"]["min"] == 30.0


_STAT_NAMES = [chr(ord("A") + i) for i in range(12)]  # avoid digits colliding with # normalization


def test_build_query_caps_at_max_stat_filters():
    mods = [ParsedMod(raw_line="", text=f"+{i} to Stat{name}", values=[float(i)]) for i, name in enumerate(_STAT_NAMES)]
    item = ParsedItem(item_class="Boots", rarity="Rare", explicit_mods=mods)
    catalog = StatCatalog.from_raw(
        [{"id": "explicit", "entries": [{"id": f"explicit.stat_{name}", "text": f"# to Stat{name}", "type": "explicit"} for name in _STAT_NAMES]}]
    )

    query = build_query(item, catalog)

    filter_ids = {f["id"] for f in query["query"]["stats"][0]["filters"]}
    assert len(query["query"]["stats"][0]["filters"]) == MAX_STAT_FILTERS
    assert len(filter_ids) == MAX_STAT_FILTERS


def test_unmapped_item_class_omits_category_filter():
    item = ParsedItem(item_class="Charms", rarity="Magic", explicit_mods=[])
    catalog = StatCatalog.from_raw([])

    query = build_query(item, catalog)

    type_filters = query["query"]["filters"]["type_filters"]["filters"]
    assert "category" not in type_filters
    assert type_filters["rarity"] == {"option": "magic"}


def test_matched_stat_ids_is_uncapped_and_unordered():
    mods = [ParsedMod(raw_line="", text=f"+{i} to Stat{name}", values=[float(i)]) for i, name in enumerate(_STAT_NAMES)]
    item = ParsedItem(item_class="Boots", rarity="Rare", explicit_mods=mods)
    catalog = StatCatalog.from_raw(
        [{"id": "explicit", "entries": [{"id": f"explicit.stat_{name}", "text": f"# to Stat{name}", "type": "explicit"} for name in _STAT_NAMES]}]
    )

    ids = matched_stat_ids(item, catalog)

    assert ids == {f"explicit.stat_{name}" for name in _STAT_NAMES}
