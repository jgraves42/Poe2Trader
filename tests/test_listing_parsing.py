from bot.trade.models import parse_listing

SAMPLE_ENTRY = {
    "id": "abc123",
    "listing": {
        "indexed": "2026-06-19T04:49:03Z",
        "price": {"type": "~price", "amount": 2, "currency": "chaos"},
        "account": {"name": "Seller#1234"},
    },
    "item": {
        "typeLine": "Burnished Ruby Ring of Raiding",
        "baseType": "Ruby Ring",
        "rarity": "Magic",
        "ilvl": 35,
        "extended": {
            "hashes": {
                "explicit": [["explicit.stat_3032590688", [1]], ["explicit.stat_3917489142", [0]]],
                "implicit": [["implicit.stat_3372524247", [0]]],
            }
        },
    },
}


def test_parse_listing_extracts_basic_fields():
    listing = parse_listing(SAMPLE_ENTRY)

    assert listing.listing_id == "abc123"
    assert listing.price_amount == 2
    assert listing.price_currency == "chaos"
    assert listing.account_name == "Seller#1234"
    assert listing.rarity == "Magic"
    assert listing.ilvl == 35
    assert listing.type_line == "Burnished Ruby Ring of Raiding"
    assert listing.base_type == "Ruby Ring"


def test_parse_listing_flattens_stat_hashes_across_groups():
    listing = parse_listing(SAMPLE_ENTRY)

    assert listing.stat_hashes == frozenset(
        {"explicit.stat_3032590688", "explicit.stat_3917489142", "implicit.stat_3372524247"}
    )


def test_parse_listing_handles_missing_extended_data():
    entry = {"id": "x", "listing": {}, "item": {}}
    listing = parse_listing(entry)
    assert listing.stat_hashes == frozenset()
