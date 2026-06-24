from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Listing:
    listing_id: str | None
    price_amount: float | None
    price_currency: str | None
    account_name: str | None
    rarity: str | None
    ilvl: int | None
    type_line: str | None
    base_type: str | None
    indexed: str | None
    price_chaos_equivalent: float | None = None
    stat_hashes: frozenset[str] = frozenset()


def _extract_stat_hashes(item: dict) -> frozenset[str]:
    hashes = (item.get("extended") or {}).get("hashes") or {}
    return frozenset(
        hash_id
        for group_hashes in hashes.values()
        for hash_id, _indices in group_hashes
    )


def parse_listing(entry: dict) -> Listing:
    listing = entry.get("listing") or {}
    item = entry.get("item") or {}
    price = listing.get("price") or {}
    account = listing.get("account") or {}

    return Listing(
        listing_id=entry.get("id"),
        price_amount=price.get("amount"),
        price_currency=price.get("currency"),
        account_name=account.get("name"),
        rarity=item.get("rarity"),
        ilvl=item.get("ilvl"),
        type_line=item.get("typeLine"),
        base_type=item.get("baseType"),
        indexed=listing.get("indexed"),
        stat_hashes=_extract_stat_hashes(item),
    )
