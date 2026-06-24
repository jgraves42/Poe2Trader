from bot.trade.ratelimit import RateLimiter


def test_parses_header_into_rules():
    limiter = RateLimiter()
    limiter.update_rules_from_header("5:10:60,15:60:300,30:300:1800")
    assert limiter.rules == [(5, 10, 60), (15, 60, 300), (30, 300, 1800)]


def test_no_wait_when_under_limit():
    limiter = RateLimiter(rules=[(5, 10, 60)])
    for i in range(4):
        limiter.record_request(when=float(i))
    assert limiter.wait_time(now=4.0) == 0.0


def test_waits_when_limit_reached_in_window():
    limiter = RateLimiter(rules=[(2, 10, 60)])
    limiter.record_request(when=0.0)
    limiter.record_request(when=1.0)
    # 2 requests already in the last 10s window as of now=2.0; oldest is at t=0.
    # Must wait until t=0 falls out of the 10s window: wait = 10 - (2.0 - 0.0) = 8.0
    assert limiter.wait_time(now=2.0) == 8.0


def test_old_requests_fall_out_of_window():
    limiter = RateLimiter(rules=[(2, 10, 60)])
    limiter.record_request(when=0.0)
    limiter.record_request(when=1.0)
    # by now=11.0 both prior requests are outside the 10s window
    assert limiter.wait_time(now=11.0) == 0.0


def test_tightest_rule_wins():
    limiter = RateLimiter(rules=[(5, 10, 60), (1, 5, 30)])
    limiter.record_request(when=0.0)
    # second rule (1 req / 5s) is violated immediately; first rule is not
    assert limiter.wait_time(now=1.0) == 4.0
