from __future__ import annotations

from statistics import median

CHAOS = "chaos"


def parse_exchange_rates(raw_result: dict) -> dict[str, float]:
    if not raw_result:
        return {}
    samples: dict[str, list[float]] = {}
    for entry in raw_result.values():
        for offer in entry.get("listing", {}).get("offers", []):
            exchange = offer.get("exchange") or {}
            item = offer.get("item") or {}
            if item.get("currency") != CHAOS:
                continue
            currency = exchange.get("currency")
            exchange_amount = exchange.get("amount")
            item_amount = item.get("amount")
            if not currency or not exchange_amount or not item_amount:
                continue
            samples.setdefault(currency, []).append(item_amount / exchange_amount)
    return {currency: median(values) for currency, values in samples.items()}


def to_chaos(amount: float | None, currency: str | None, rates: dict[str, float]) -> float | None:
    if amount is None or currency is None:
        return None
    if currency == CHAOS:
        return amount
    rate = rates.get(currency)
    if rate is None:
        return None
    return amount * rate
