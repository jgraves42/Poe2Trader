from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParsedMod:
    raw_line: str
    text: str
    tags: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclass
class ParsedItem:
    item_class: str | None = None
    rarity: str | None = None
    name: str | None = None
    base_type: str | None = None

    quality: float | None = None
    armour: float | None = None
    evasion: float | None = None
    energy_shield: float | None = None
    spirit: float | None = None
    physical_damage: tuple[float, float] | None = None
    elemental_damage: list[tuple[float, float]] = field(default_factory=list)
    attacks_per_second: float | None = None
    critical_hit_chance: float | None = None

    requirements: dict[str, float] = field(default_factory=dict)
    sockets: list[str] = field(default_factory=list)
    item_level: int | None = None

    enchant_mods: list[ParsedMod] = field(default_factory=list)
    rune_mods: list[ParsedMod] = field(default_factory=list)
    implicit_mods: list[ParsedMod] = field(default_factory=list)
    explicit_mods: list[ParsedMod] = field(default_factory=list)

    corrupted: bool = False
    unidentified: bool = False
    mirrored: bool = False

    raw_text: str = ""

    @property
    def all_mods(self) -> list[ParsedMod]:
        return [*self.enchant_mods, *self.rune_mods, *self.implicit_mods, *self.explicit_mods]
