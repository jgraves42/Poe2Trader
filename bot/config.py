import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
POE2_LEAGUE = os.environ.get("POE2_LEAGUE", "HC Runes of Aldur")
POE_SESSION_ID = os.environ.get("POE_SESSION_ID", "")
