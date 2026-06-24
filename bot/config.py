import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
POE2_LEAGUE = os.environ.get("POE2_LEAGUE", "HC Runes of Aldur")
POE_SESSION_ID = os.environ.get("POE_SESSION_ID", "")

_channel_id_raw = os.environ.get("PRICECHECK_CHANNEL_ID")
PRICECHECK_CHANNEL_ID: int | None = int(_channel_id_raw) if _channel_id_raw else None
