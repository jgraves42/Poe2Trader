from pathlib import Path

from bot.parser import parse_item

SAMPLES_DIR = Path(__file__).parent / "samples"


def load(name: str) -> str:
    return (SAMPLES_DIR / name).read_text()


def test_rare_boots():
    item = parse_item(load("rare_boots.txt"))

    assert item.item_class == "Boots"
    assert item.rarity == "Rare"
    assert item.name == "Stormrider Boots"
    assert item.base_type == "Advanced Dualstring Boots"
    assert item.quality == 20.0
    assert item.armour == 150.0
    assert item.evasion == 120.0
    assert item.requirements == {"level": 65.0, "str": 100.0, "dex": 100.0}
    assert item.sockets == ["S", "S"]
    assert item.item_level == 76
    assert not item.corrupted
    assert not item.unidentified

    explicit_texts = [m.text for m in item.explicit_mods]
    assert "30% increased Movement Speed" in explicit_texts
    life_mod = next(m for m in item.explicit_mods if "maximum Life" in m.text)
    assert life_mod.values == [85.0]
    assert len(item.explicit_mods) == 5


def test_rare_body_armour_prestige_mod_present():
    item = parse_item(load("rare_body_armour_prestige.txt"))

    assert item.energy_shield == 250.0
    assert item.spirit == 100.0

    prestige_mod = next(m for m in item.explicit_mods if "Level of all Skill Gems" in m.text)
    assert prestige_mod.values == [1.0]
    assert prestige_mod.tags == []


def test_magic_ring_implicit_and_explicit_split():
    item = parse_item(load("magic_ring.txt"))

    assert item.rarity == "Magic"
    assert item.name is None
    assert item.base_type == "Stinging Coral Ring"
    assert item.requirements == {"level": 24.0}

    assert len(item.implicit_mods) == 1
    assert item.implicit_mods[0].values == [20.0]
    assert "implicit" in item.implicit_mods[0].tags

    assert len(item.explicit_mods) == 1
    assert item.explicit_mods[0].values == [25.0]


def test_unique_item_separates_implicit_from_explicit():
    item = parse_item(load("unique_item.txt"))

    assert item.rarity == "Unique"
    assert item.name == "Crystal Skull"
    assert item.base_type == "Spiked Gloves"
    assert len(item.implicit_mods) == 1
    assert len(item.explicit_mods) == 3
    assert item.sockets == ["S", "S"]


def test_corrupted_weapon():
    item = parse_item(load("corrupted_weapon.txt"))

    assert item.corrupted is True
    assert item.physical_damage == (25.0, 48.0)
    assert item.critical_hit_chance == 6.5
    assert item.attacks_per_second == 1.45

    fire_mod = next(m for m in item.explicit_mods if "Fire Damage" in m.text)
    assert fire_mod.values == [12.0, 18.0]


def test_unidentified_item():
    item = parse_item(load("unidentified_item.txt"))

    assert item.unidentified is True
    assert item.name is None
    assert item.base_type == "Advanced Dualstring Boots"
    assert item.explicit_mods == []
    assert item.implicit_mods == []
