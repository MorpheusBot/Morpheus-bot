from __future__ import annotations

import os
from os.path import isdir, isfile
from typing import TYPE_CHECKING

import discord

from config.app_config import config
from utils.general import split

from .messages import SystemMess

if TYPE_CHECKING:
    from morpheus import Morpheus


def get_all_cogs() -> list[tuple[str, str]]:
    """Get all cog modules

    Returns:
    --------
    List[cog name, path]
    """
    path = "./cogs"
    all_cogs = []

    for name in os.listdir(path):
        if not isdir(f"{path}/{name}"):
            continue

        if not isfile(f"{path}/{name}/__init__.py"):
            continue

        all_cogs.append((name, f"{path}/{name}"))

    return sorted(all_cogs)


async def split_cogs() -> list[tuple[str, str]]:
    """Slices list of all cogs to chunks for select.

    Returns:
    --------
    List[cog name, path]
    """
    cog_pairs = get_all_cogs()
    all_cogs = []
    pairs_count = len(cog_pairs)
    chunk_size = 25

    for i in range(0, len(cog_pairs), chunk_size):
        pairs = cog_pairs[i : min(i + chunk_size, pairs_count)]
        all_cogs.append(pairs)

    return all_cogs


def create_embed(bot: Morpheus) -> discord.Embed:
    embed = discord.Embed(title=SystemMess.embed_title, colour=discord.Color.yellow())
    bot_cogs = [cog.lower() for cog in bot.cogs]
    cogs = get_all_cogs()
    cog_count = len(cogs)

    cog_loaded = []
    cog_unloaded = []
    for cog_name, _ in cogs:
        name = cog_name.title()
        if cog_name in bot_cogs:
            if cog_name not in config.extensions:
                name = f"{name}"
            cog_loaded.append(f"✅ {name}\n\n")
        else:
            if cog_name in config.extensions:
                name = f"{name}"
            cog_unloaded.append(f"❌ {name}\n\n")

    loaded_count = len(cog_loaded)
    unloaded_count = len(cog_unloaded)

    embed.description = SystemMess.embed_description(loaded=loaded_count, unloaded=unloaded_count, all=cog_count)

    chunks_count = 2 if cog_count <= 20 else 3

    loaded_chunks = split(cog_loaded, chunks_count)
    unloaded_chunks = split(cog_unloaded, chunks_count)

    for loaded_chunk in loaded_chunks:
        embed.add_field(name="\u200b", value="".join(loaded_chunk), inline=True)

    # separator
    if unloaded_chunks:
        embed.add_field(name="\u200b", value="", inline=False)

    for unloaded_chunk in unloaded_chunks:
        embed.add_field(name="\u200b", value="".join(unloaded_chunk), inline=True)

    embed.set_footer(text=SystemMess.override)
    return embed
