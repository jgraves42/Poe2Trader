from bot.trade.models import Listing
from bot.trade.similarity import similarity_count, sort_by_similarity


def make_listing(listing_id: str, price: float | None, stat_hashes: frozenset[str]) -> Listing:
    return Listing(
        listing_id=listing_id,
        price_amount=price,
        price_currency="chaos",
        account_name=None,
        rarity=None,
        ilvl=None,
        type_line=None,
        base_type=None,
        indexed=None,
        price_chaos_equivalent=price,
        stat_hashes=stat_hashes,
    )


def test_similarity_count_is_intersection_size():
    listing = make_listing("a", 1.0, frozenset({"explicit.life", "explicit.fire_res"}))
    reference = {"explicit.life", "explicit.cold_res"}
    assert similarity_count(listing, reference) == 1


def test_similarity_count_zero_when_no_overlap():
    listing = make_listing("a", 1.0, frozenset({"explicit.attack_speed"}))
    reference = {"explicit.life"}
    assert similarity_count(listing, reference) == 0


def test_sort_by_similarity_ranks_most_matching_first():
    reference = {"explicit.life", "explicit.fire_res", "explicit.move_speed"}
    low_match = make_listing("low", 1.0, frozenset({"explicit.life"}))
    high_match = make_listing("high", 10.0, frozenset({"explicit.life", "explicit.fire_res", "explicit.move_speed"}))
    mid_match = make_listing("mid", 2.0, frozenset({"explicit.life", "explicit.fire_res"}))

    ranked = sort_by_similarity([low_match, mid_match, high_match], reference)

    assert [listing.listing_id for listing in ranked] == ["high", "mid", "low"]


def test_sort_by_similarity_uses_price_as_tiebreaker():
    reference = {"explicit.life"}
    cheaper = make_listing("cheap", 1.0, frozenset({"explicit.life"}))
    pricier = make_listing("pricey", 5.0, frozenset({"explicit.life"}))

    ranked = sort_by_similarity([pricier, cheaper], reference)

    assert [listing.listing_id for listing in ranked] == ["cheap", "pricey"]
