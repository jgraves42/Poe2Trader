import discord
from discord import app_commands
from discord.ext import commands

from bot.config import POE2_LEAGUE, POE_SESSION_ID, PRICECHECK_CHANNEL_ID
from bot.parser import ParsedItem, parse_item
from bot.trade import Listing, TradeClient, build_basetype_query, build_query, matched_stat_ids, similarity_count, sort_by_similarity, stat_id_text_map
from bot.trade.category_map import get_category

PASTE_TIMEOUT_SECONDS = 120
TARGET_LISTING_COUNT = 30
MAX_LISTINGS_SHOWN = 5


def format_parsed_item(item: ParsedItem) -> str:
    lines = [f"**{item.name or item.base_type}** ({item.rarity}, {item.item_class})"]
    if item.name:
        lines.append(f"Base: {item.base_type}")
    if item.item_level is not None:
        lines.append(f"Item Level: {item.item_level}")
    if item.sockets:
        lines.append(f"Sockets: {' '.join(item.sockets)}")
    if item.corrupted:
        lines.append("Corrupted")
    if item.unidentified:
        lines.append("Unidentified")

    def mod_lines(label: str, mods) -> list[str]:
        return [f"  [{label}] {mod.text}" for mod in mods]

    lines += mod_lines("enchant", item.enchant_mods)
    lines += mod_lines("rune", item.rune_mods)
    lines += mod_lines("implicit", item.implicit_mods)
    lines += mod_lines("explicit", item.explicit_mods)

    return "\n".join(lines)


def format_listings(
    item: ParsedItem,
    listings: list[Listing],
    reference_stat_ids: set[str],
    id_to_text: dict[str, str],
    *,
    fallback: bool = False,
) -> str:
    label = item.name or item.base_type
    if not listings:
        return f"No listings found for **{label}** ({item.rarity})."

    total_mods = len(reference_stat_ids)

    if fallback:
        lines = [f"No mod matches — top {MAX_LISTINGS_SHOWN} listings for **{item.base_type}** (same base, sorted by price)"]
    else:
        header = f"Top {MAX_LISTINGS_SHOWN} closest matches for **{label}** ({item.rarity})"
        if get_category(item.item_class) is None:
            header += " _(no category filter)_"
        lines = [header]

    for listing in listings[:MAX_LISTINGS_SHOWN]:
        matched_ids = listing.stat_hashes & reference_stat_ids
        score = len(matched_ids)

        if fallback or score == 0:
            price = "—"
        elif listing.price_amount is None:
            price = "no price set"
        else:
            price = f"{listing.price_amount:g} {listing.price_currency}"

        score_str = f"{score}/{total_mods} mods" if total_mods else ""
        name = listing.type_line or listing.base_type or "Unknown"
        lines.append(f"\n**{name}** (lvl {listing.ilvl}) — {price}  [{score_str}]")

        for stat_id in matched_ids:
            mod_text = id_to_text.get(stat_id, stat_id)
            lines.append(f"  • {mod_text}")

    return "\n".join(lines)



class PriceCheck(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.trade_client = TradeClient(POE2_LEAGUE, session_id=POE_SESSION_ID)
        self.stat_catalog = None

    async def cog_load(self) -> None:
        self.stat_catalog = await self.trade_client.load_stats()

    async def cog_unload(self) -> None:
        await self.trade_client.aclose()

    @app_commands.command(name="pricecheck", description="Price check a PoE2 item")
    async def pricecheck(self, interaction: discord.Interaction) -> None:
        if PRICECHECK_CHANNEL_ID is not None and interaction.channel_id != PRICECHECK_CHANNEL_ID:
            await interaction.response.send_message(
                f"Please use <#{PRICECHECK_CHANNEL_ID}> for price checks.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Paste your item text (Ctrl+C in-game) in this channel within "
            f"{PASTE_TIMEOUT_SECONDS} seconds.",
            ephemeral=True,
        )

        def check(message: discord.Message) -> bool:
            return message.author.id == interaction.user.id and message.channel.id == interaction.channel_id

        try:
            message = await self.bot.wait_for("message", check=check, timeout=PASTE_TIMEOUT_SECONDS)
        except TimeoutError:
            await interaction.followup.send("Timed out waiting for an item paste.", ephemeral=True)
            return

        item = parse_item(message.content)
        if item.item_class is None:
            await interaction.followup.send(
                "Couldn't parse that as an item — make sure you pasted the full item text.",
                ephemeral=True,
            )
            return

        query = build_query(item, self.stat_catalog)
        reference_stat_ids = matched_stat_ids(item, self.stat_catalog)
        id_to_text = stat_id_text_map(item, self.stat_catalog)
        query_id, listings = await self.trade_client.search_and_fetch(query, target_count=TARGET_LISTING_COUNT)
        listings = sort_by_similarity(listings, reference_stat_ids)

        no_similarities = all(similarity_count(l, reference_stat_ids) == 0 for l in listings)
        if no_similarities and item.base_type:
            fallback_query = build_basetype_query(item)
            _, fallback_listings = await self.trade_client.search_and_fetch(fallback_query, target_count=TARGET_LISTING_COUNT)
            listings_block = format_listings(item, fallback_listings, reference_stat_ids, id_to_text, fallback=True)
        else:
            listings_block = format_listings(item, listings, reference_stat_ids, id_to_text)

        reply = listings_block
        await message.reply(reply)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PriceCheck(bot))
