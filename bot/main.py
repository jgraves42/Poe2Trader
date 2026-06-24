import logging

import discord
from discord.ext import commands

from bot.config import DISCORD_BOT_TOKEN

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("poe2_pricer")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.tree.sync()
    log.info("Logged in as %s (id=%s)", bot.user, bot.user.id)


async def setup_hook() -> None:
    await bot.load_extension("bot.cogs.pricecheck")


bot.setup_hook = setup_hook


def run() -> None:
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    run()
