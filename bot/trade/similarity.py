from __future__ import annotations

from .models import Listing


def similarity_count(listing: Listing, reference_stat_ids: set[str]) -> int:
    return len(listing.stat_hashes & reference_stat_ids)


def sort_by_similarity(listings: list[Listing], reference_stat_ids: set[str]) -> list[Listing]:
    def sort_key(listing: Listing) -> tuple[int, float]:
        price = listing.price_chaos_equivalent if listing.price_chaos_equivalent is not None else float("inf")
        return (-similarity_count(listing, reference_stat_ids), price)

    return sorted(listings, key=sort_key)
