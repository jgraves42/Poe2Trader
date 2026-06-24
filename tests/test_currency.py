from bot.trade.currency import parse_exchange_rates, to_chaos


def test_parse_exchange_rates_computes_chaos_per_unit():
    raw_result = {
        "entry1": {
            "listing": {
                "offers": [
                    {
                        "exchange": {"currency": "exalted", "amount": 15},
                        "item": {"currency": "chaos", "amount": 1},
                    }
                ]
            }
        },
        "entry2": {
            "listing": {
                "offers": [
                    {
                        "exchange": {"currency": "exalted", "amount": 20},
                        "item": {"currency": "chaos", "amount": 1},
                    }
                ]
            }
        },
    }

    rates = parse_exchange_rates(raw_result)

    # median (= mean of these two) of (1/15, 1/20) chaos-per-exalted
    assert rates["exalted"] == (1 / 15 + 1 / 20) / 2


def test_parse_exchange_rates_ignores_offers_not_priced_in_chaos():
    raw_result = {
        "entry1": {
            "listing": {
                "offers": [
                    {
                        "exchange": {"currency": "exalted", "amount": 5},
                        "item": {"currency": "divine", "amount": 1},
                    }
                ]
            }
        }
    }

    assert parse_exchange_rates(raw_result) == {}


def test_to_chaos_for_chaos_currency_is_identity():
    assert to_chaos(5.0, "chaos", {}) == 5.0


def test_to_chaos_converts_using_rate():
    rates = {"exalted": 1 / 15}
    assert to_chaos(15.0, "exalted", rates) == 1.0


def test_to_chaos_returns_none_when_rate_unknown():
    assert to_chaos(5.0, "annul", {}) is None


def test_to_chaos_returns_none_for_missing_amount_or_currency():
    assert to_chaos(None, "chaos", {}) is None
    assert to_chaos(5.0, None, {}) is None
