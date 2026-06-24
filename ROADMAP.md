# Roadmap — Phases 3-6

Phase 1 (bot skeleton) and Phase 2 (item parser) are done — see `bot/`, `tests/`.
This doc captures what's needed to build the rest without re-deriving context.

## Phase 3 — Trade API Layer

PoE2 trade lives at `pathofexile.com/trade2`. It's not in GGG's official dev docs
(`pathofexile.com/developer/docs/reference` only covers account/league/stash data),
so this is the same unofficial-but-widely-used surface PoE1 tools have always used.

**Two-step query flow:**
1. `POST https://www.pathofexile.com/api/trade2/search/<league>` with a JSON query
   body (filters built from parsed mods) → returns a search `id` and a list of result
   listing IDs (often hundreds; paginate/slice client-side).
2. `GET https://www.pathofexile.com/api/trade2/fetch/<comma-separated-ids>?query=<id>`
   → returns full listing details (price, account, item) for up to ~10 IDs per call.

**Stat ID mapping — do this first, before the query constructor:**
`GET https://www.pathofexile.com/api/trade2/data/stats` returns every filterable stat
with its trade API ID and matching display text/regex. Parsed mod text must be matched
against this list (fuzzy/regex match on the mod text template, e.g. `"+# to maximum
Life"`) to get the correct stat ID for the query — IDs can't be hardcoded since they're
internal GGG identifiers. Fetch once at startup, cache to disk (it rarely changes
within a league), refresh on a long TTL (e.g. daily).

**Rate limiting — GGG blocks aggressively:**
- Read `X-Rate-Limit-Rules`, `X-Rate-Limit-Account`, `X-Rate-Limit-Ip` response
  headers and self-throttle to stay under the disclosed limits rather than waiting
  for a 429.
- On 429, respect `Retry-After` exactly; back off the whole client, not just the one
  request.
- Use one shared `httpx.AsyncClient` with a realistic `User-Agent` (GGG has blocked
  generic/default user agents historically) and a request queue/semaphore so
  concurrent `/pricecheck` calls from different Discord users don't burst the API.
- `POE_SESSION_ID` (already wired as an optional env var in `bot/config.py`) can be
  sent as a `POESESSID` cookie if/when available — test whether it changes effective
  rate limits or unlocks anything the parser needs; not required to get started.

**Sampling:** aim for 30-50 listings per query (per the original plan) — request more
IDs from step 1 than you fetch, then fetch in batches of ~10 via step 2 until you hit
the target count or run out of results.

**Caching:** short TTL (minutes, not hours — prices move) in-memory cache keyed by a
normalized representation of the query (sorted stat IDs + rounded value ranges), so
repeated `/pricecheck` calls for similar items don't re-hit the API.

## Phase 4 — Pricing Engine

Implements the two-axis model from the mod-tier reference doc (already in this
project's context — re-read it before implementing, it's the spec):

- Score every parsed mod on **Slot Relevance** (0.0-1.0, per the Slot Chase
  Short-List table) and **Global Value Weight** (the S/A/B/C tier multipliers).
- `if global_weight >= PRESTIGE_THRESHOLD and slot_relevance < 0.3:` → isolate into a
  prestige bucket (flat premium, reported separately) instead of blending into the
  weighted average. Pick `PRESTIGE_THRESHOLD` empirically once real trade data is
  flowing (start around `1.8-2.0`, tune against observed listing prices).
- Weight rare listings far above magic in the base average; feed magic listings that
  carry an S-tier mod into the *same* prestige bucket as rares with that mod (per the
  "magic outliers bump rares" rule), don't just discard them.
- Demand classification from listing count (sparse/moderate/flooded) as a modest ±
  adjustment on top of the base+premium price — never the dominant term.
- Confidence: widen the quoted range and flag low confidence below ~8 comparable
  listings.
- Tiers: if the trade API response exposes mod tier/range data, factor it in — a T1
  roll and a T7 roll of "the same mod" are not comparable.

## Phase 5 — Discord Response Formatting

- Build a `discord.Embed` (replacing the plain-text dump in `pricecheck.py` from
  Phase 1) with: price estimate, confidence range, and bullet-point reasoning.
- Reasoning must name specific driver mods, rarity tier, and demand class — e.g.
  "Base ~12 ex from Life + dual resist; +2 Projectile Gems detected → prestige
  premium ×2.4 → est. 28-35 ex." This is the "always show why" rule from the
  reference doc — don't just output a number.

## Phase 6 — Hosting

- Push to GitHub (this repo has no remote yet — confirm with the user before adding
  one or pushing).
- Railway deploy: this is a long-running bot process (`bot.main.run()`), **not** a web
  server. Configure the Railway service as a worker — no HTTP port, no health check
  expecting a listening socket, or Railway will mark deploys unhealthy.
- Set `DISCORD_BOT_TOKEN`, `POE2_LEAGUE`, `POE_SESSION_ID` in the Railway dashboard's
  environment variables, not committed to the repo (`.env` is already gitignored).
