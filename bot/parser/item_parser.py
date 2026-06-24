from __future__ import annotations

import re

from .models import ParsedItem, ParsedMod

_SEPARATOR = re.compile(r"^-{4,}$")
_TAG = re.compile(r"\((implicit|enchant|rune|crafted|fractured)\)", re.IGNORECASE)
_NUMBER = re.compile(r"[-+]?\d+\.?\d*")
_NUMBER_RANGE = re.compile(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)")
_FOOTER_FLAGS = {"corrupted", "unidentified", "mirrored"}

_STAT_KEYS = {
    "quality": "quality",
    "armour": "armour",
    "evasion rating": "evasion",
    "evasion": "evasion",
    "energy shield": "energy_shield",
    "spirit": "spirit",
    "critical hit chance": "critical_hit_chance",
    "attacks per second": "attacks_per_second",
}


def _split_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if _SEPARATOR.match(line):
            if current:
                blocks.append(current)
                current = []
            continue
        if line:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _parse_header(block: list[str], item: ParsedItem) -> None:
    for line in block:
        if line.startswith("Item Class:"):
            item.item_class = line.split(":", 1)[1].strip()
        elif line.startswith("Rarity:"):
            item.rarity = line.split(":", 1)[1].strip()
        elif item.name is None and item.base_type is None:
            item.name = line
        elif item.base_type is None:
            item.base_type = line
    if item.base_type is None and item.name is not None:
        item.base_type = item.name
        item.name = None


def _parse_numeric_range(value: str) -> tuple[float, float]:
    range_match = _NUMBER_RANGE.search(value)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))
    single = _NUMBER.search(value)
    if single:
        return float(single.group()), float(single.group())
    return (0.0, 0.0)


def _is_stats_block(block: list[str]) -> bool:
    for line in block:
        key = line.split(":", 1)[0].strip().lower()
        if key in _STAT_KEYS or key in ("physical damage", "elemental damage", "fire damage", "cold damage", "lightning damage", "chaos damage"):
            return True
    return False


def _parse_stats(block: list[str], item: ParsedItem) -> None:
    for line in block:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in _STAT_KEYS:
            match = _NUMBER.search(value)
            if match:
                setattr(item, _STAT_KEYS[key], float(match.group()))
        elif key == "physical damage":
            item.physical_damage = _parse_numeric_range(value)
        elif key in ("elemental damage", "fire damage", "cold damage", "lightning damage", "chaos damage"):
            item.elemental_damage.append(_parse_numeric_range(value))


def _parse_requirements(block: list[str], item: ParsedItem) -> None:
    joined = " ".join(block)
    joined = joined.split(":", 1)[1] if joined.startswith("Requires") and ":" in joined else joined
    level_match = re.search(r"Level[:\s]+(\d+)", joined, re.IGNORECASE)
    if level_match:
        item.requirements["level"] = float(level_match.group(1))
    for attr, pattern in (("str", r"(\d+)\s*Str"), ("dex", r"(\d+)\s*Dex"), ("int", r"(\d+)\s*Int")):
        match = re.search(pattern, joined, re.IGNORECASE)
        if match:
            item.requirements[attr] = float(match.group(1))


def _parse_mod_line(line: str) -> ParsedMod:
    tags = [t.lower() for t in _TAG.findall(line)]
    text = _TAG.sub("", line).strip()
    values = [float(v) for v in _NUMBER.findall(text)]
    return ParsedMod(raw_line=line, text=text, tags=tags, values=values)


def parse_item(raw_text: str) -> ParsedItem:
    item = ParsedItem(raw_text=raw_text)
    blocks = _split_blocks(raw_text)

    for index, block in enumerate(blocks):
        first_line_lower = block[0].lower()

        if index == 0 and block[0].startswith("Item Class:"):
            _parse_header(block, item)
            continue

        if len(block) == 1 and block[0].strip().lower() in _FOOTER_FLAGS:
            flag = block[0].strip().lower()
            setattr(item, flag, True)
            continue

        if first_line_lower.startswith("requires"):
            _parse_requirements(block, item)
            continue

        if first_line_lower.startswith("sockets:"):
            item.sockets = block[0].split(":", 1)[1].strip().split()
            continue

        if first_line_lower.startswith("item level:"):
            match = _NUMBER.search(block[0])
            if match:
                item.item_level = int(float(match.group()))
            continue

        if _is_stats_block(block):
            _parse_stats(block, item)
            continue

        mods = [_parse_mod_line(line) for line in block]
        for mod in mods:
            if "enchant" in mod.tags:
                item.enchant_mods.append(mod)
            elif "rune" in mod.tags:
                item.rune_mods.append(mod)
            elif "implicit" in mod.tags:
                item.implicit_mods.append(mod)
            else:
                item.explicit_mods.append(mod)

    return item
