from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from cogs.base import Base

if TYPE_CHECKING:
    from morpheus import Morpheus


class Instagram(Base, commands.Cog):
    """Cog for handling Instagram URL embeds."""

    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        # Pattern to match any Instagram URLs (simple domain-based matching)
        self.instagram_pattern = re.compile(r"(?:https://)?(?:www\.)?instagram\.com/[^\s]+")

    @commands.Cog.listener("on_message")
    async def on_message_instagram(self, message: discord.Message) -> None:
        """
        Listens for messages containing Instagram URLs.
        When found, deletes the original message and reposts with 'kk' prefix for better embedding.
        """
        # Ignore bot messages
        if message.author.bot:
            return

        # Ignore DMs
        if message.guild is None:
            return

        # Search for Instagram URLs in the message
        instagram_urls = self.instagram_pattern.findall(message.content)

        if not instagram_urls:
            return

        try:
            # Delete the original message
            await message.delete()

            # Replace all instagram.com domains with kkinstagram.com in one pass
            repost_content = self.instagram_pattern.sub(
                lambda m: m.group(0).replace("instagram.com", "kkinstagram.com"),
                message.content,
            )

            await message.channel.send(f"{message.author.mention} >> {repost_content}")

        except discord.Forbidden:
            # Bot doesn't have permission to delete messages
            pass
        except discord.HTTPException:
            # Something went wrong with the API request
            pass
