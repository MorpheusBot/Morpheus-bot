from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base

from .messages import GayMess

if TYPE_CHECKING:
    from morpheus import Morpheus

mention_count = {}
mention_author_count = {}


def first_in_day(message, prev_message_day):
    if prev_message_day is None:
        return True
    # WARN: Can be wrong if the next message is month after at the same day
    return message.created_at.day != prev_message_day


async def iterate_messages(channel):
    history = await channel.history(limit=None).flatten()
    prev_message_day = None
    for message in history:
        if message.author.bot:
            continue

        if not first_in_day(message, prev_message_day):
            continue

        if not len(message.mentions):
            continue

        for mention in message.mentions:
            if mention not in mention_count:
                mention_count[mention] = 0
            mention_count[mention] += 1

        if message.author not in mention_author_count:
            mention_author_count[message.author] = 0
        mention_author_count[message.author] += 1
        prev_message_day = message.created_at.day


class Gay(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot

    @app_commands.guilds(Base.config.guild_id)
    @app_commands.command(name="leadgay", description=GayMess.leadgay_brief)
    async def gays(self, inter: discord.Interaction, count: app_commands.Range[int, 1] = 10):
        global mention_author_count, mention_count
        mention_author_count = {}
        mention_count = {}
        await inter.response.defer()
        channel = Base.base_guild.get_channel(Base.config.gay_channel)
        if isinstance(channel, discord.TextChannel):
            await iterate_messages(channel)

        mention_count_sorted = dict(sorted(mention_count.items(), key=lambda item: item[1], reverse=True)[:count])

        gays = ""
        for mention, tag_count in mention_count_sorted.items():
            gays += f"{mention.name}: {tag_count}\n"
        message_gays = GayMess.best_gays(gays=gays)

        mention_author_count_sorted = dict(
            sorted(mention_author_count.items(), key=lambda item: item[1], reverse=True)[:count]
        )

        taggers = ""
        for mention, tag_count in mention_author_count_sorted.items():
            taggers += f"{mention.name}: {tag_count}\n"
        message_taggers = GayMess.best_taggers(taggers=taggers)

        await inter.edit_original_response(message_gays + message_taggers)
