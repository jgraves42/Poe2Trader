from __future__ import annotations

import time


class RateLimiter:
    def __init__(self, rules: list[tuple[int, int, int]] | None = None) -> None:
        self.rules: list[tuple[int, int, int]] = rules or []
        self._timestamps: list[float] = []

    def update_rules_from_header(self, header_value: str) -> None:
        rules = []
        for part in header_value.split(","):
            limit, window, penalty = (int(x) for x in part.split(":"))
            rules.append((limit, window, penalty))
        self.rules = rules

    def record_request(self, when: float | None = None) -> None:
        self._timestamps.append(when if when is not None else time.monotonic())

    def wait_time(self, now: float | None = None) -> float:
        if not self.rules:
            return 0.0
        now = now if now is not None else time.monotonic()
        wait = 0.0
        for limit, window, _penalty in self.rules:
            recent = [t for t in self._timestamps if now - t < window]
            if len(recent) >= limit:
                oldest = min(recent)
                wait = max(wait, window - (now - oldest))
        return max(wait, 0.0)
