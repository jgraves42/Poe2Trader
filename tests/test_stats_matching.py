from pathlib import Path

from bot.parser import ParsedMod, parse_item
from bot.trade.stats import StatCatalog

SAMPLES_DIR = Path(__file__).parent / "samples"

FIXTURE_GROUPS = [
    {
        "id": "explicit",
        "entries": [
            {"id": "explicit.stat_movespeed", "text": "#% increased Movement Speed", "type": "explicit"},
            {"id": "explicit.stat_life", "text": "# to maximum Life", "type": "explicit"},
            {"id": "explicit.stat_fireres", "text": "#% to Fire Resistance", "type": "explicit"},
            {"id": "explicit.stat_gemlevel", "text": "# to Level of all Skill Gems", "type": "explicit"},
        ],
    },
    {
        "id": "implicit",
        "entries": [
            {"id": "implicit.stat_ringlife", "text": "# to maximum Life", "type": "implicit"},
        ],
    },
]


def catalog() -> StatCatalog:
    return StatCatalog.from_raw(FIXTURE_GROUPS)


def test_matches_simple_percent_mod():
    mod = ParsedMod(raw_line="", text="30% increased Movement Speed", values=[30.0])
    assert catalog().match(mod, "explicit") == "explicit.stat_movespeed"


def test_matches_flat_value_mod():
    mod = ParsedMod(raw_line="", text="+85 to maximum Life", values=[85.0])
    assert catalog().match(mod, "explicit") == "explicit.stat_life"


def test_matches_prestige_mod():
    mod = ParsedMod(raw_line="", text="+1 to Level of all Skill Gems", values=[1.0])
    assert catalog().match(mod, "explicit") == "explicit.stat_gemlevel"


def test_falls_back_to_other_group_when_preferred_group_lacks_entry():
    mod = ParsedMod(raw_line="", text="+20 to maximum Life", values=[20.0])
    implicit_only_catalog = StatCatalog.from_raw(
        [{"id": "implicit", "entries": [{"id": "implicit.stat_ringlife", "text": "# to maximum Life", "type": "implicit"}]}]
    )
    assert implicit_only_catalog.match(mod, "explicit") == "implicit.stat_ringlife"


def test_no_match_returns_none():
    mod = ParsedMod(raw_line="", text="Some Unknown Mod Text", values=[])
    assert catalog().match(mod, "explicit") is None


def test_real_parsed_item_mods_match_catalog():
    item = parse_item((SAMPLES_DIR / "rare_boots.txt").read_text())
    life_mod = next(m for m in item.explicit_mods if "maximum Life" in m.text)
    assert catalog().match(life_mod, "explicit") == "explicit.stat_life"
