"""
Cog for managing server emojis. Download emojis and stickers. Get full size of emoji.
"""

from __future__ import annotations

import io
import os
import zipfile
from datetime import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.base import Base
from custom import room_check
from custom.cooldowns import default_cooldown
from utils.general import get_local_zone

from .messages import EmojiMess

if TYPE_CHECKING:
    from morpheus import Morpheus


@default_cooldown()
class EmojiGroup(app_commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Emoji(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.download_emojis_task.start()]
        self.check = room_check.RoomCheck(bot)

    emoji = EmojiGroup(name="emoji", description=EmojiMess.emoji_brief)

    async def download_emojis(self, guild: discord.Guild):
        """Download all emojis from server and save them to zip file"""
        emojis = await guild.fetch_emojis()
        stickers = await guild.fetch_stickers()
        with zipfile.ZipFile("emojis.zip", "w") as zip_file:
            for emoji in emojis:
                with io.BytesIO() as image_binary:
                    if emoji.animated:
                        emoji_name = f"emojis/{emoji.name}.gif"
                    else:
                        emoji_name = f"emojis/{emoji.name}.png"
                    await emoji.save(image_binary)
                    zip_file.writestr(emoji_name, image_binary.getvalue())

            for sticker in stickers:
                with io.BytesIO() as image_binary:
                    sticker_name = f"stickers/{sticker.name}.{sticker.format.name}"
                    await sticker.save(image_binary)
                    zip_file.writestr(sticker_name, image_binary.getvalue())

    @emoji.command(name="get_emojis", description=EmojiMess.get_emojis_brief)
    async def get_emojis(self, inter: discord.Interaction):
        """Get all emojis from server"""
        await inter.response.defer()
        if not os.path.exists("emojis.zip"):
            await self.download_emojis(inter.guild)
        await inter.edit_original_response(file=discord.File("emojis.zip"))

    @emoji.command(name="get_emoji", description=EmojiMess.get_emoji_brief)
    async def get_emoji(self, inter: discord.Interaction, emoji: str):
        """Get emoji in full size"""
        await inter.response.defer()
        emoji = discord.PartialEmoji.from_str(emoji)
        await inter.edit_original_response(emoji.url)

    @tasks.loop(time=time(5, 0, tzinfo=get_local_zone()))
    async def download_emojis_task(self):
        await self.download_emojis(self.base_guild)

    @get_emoji.error
    async def emoji_errors(self, inter: discord.Interaction, error):
        if isinstance(error, commands.PartialEmojiConversionFailure):
            await inter.send(EmojiMess.invalid_emoji, ephemeral=True)
            return True
