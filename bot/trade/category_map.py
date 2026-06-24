_CATEGORY_BY_ITEM_CLASS = {
    "Boots": "armour.boots",
    "Gloves": "armour.gloves",
    "Helmets": "armour.helmet",
    "Body Armours": "armour.chest",
    "Shields": "armour.shield",
    "Quivers": "armour.quiver",
    "Rings": "accessory.ring",
    "Amulets": "accessory.amulet",
    "Belts": "accessory.belt",
    "Jewels": "jewel",
    "One Hand Swords": "weapon.onesword",
    "Two Hand Swords": "weapon.twosword",
    "One Hand Axes": "weapon.oneaxe",
    "Two Hand Axes": "weapon.twoaxe",
    "One Hand Maces": "weapon.onemace",
    "Two Hand Maces": "weapon.twomace",
    "Bows": "weapon.bow",
    "Wands": "weapon.wand",
    "Staves": "weapon.staff",
    "Claws": "weapon.claw",
    "Daggers": "weapon.dagger",
    "Sceptres": "weapon.sceptre",
}


def get_category(item_class: str | None) -> str | None:
    if item_class is None:
        return None
    return _CATEGORY_BY_ITEM_CLASS.get(item_class)
