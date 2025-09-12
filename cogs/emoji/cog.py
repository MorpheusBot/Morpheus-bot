"""
Cog for managing server emojis. Download emojis and stickers. Get full size of emoji.
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from datetime import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

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


class PartialEmojiTransformer(discord.PartialEmoji):
    @classmethod
    async def transform(cls, interaction: discord.Interaction, emoji: str) -> discord.PartialEmoji:
        ctx = await commands.Context.from_interaction(interaction)
        try:
            return await commands.PartialEmojiConverter().convert(ctx, emoji)
        except commands.PartialEmojiConversionFailure:
            # Emoji from url
            match = re.search(r"/emojis/(\d+)", emoji)
            if match:
                emoji_id = int(match.group(1))
                return discord.PartialEmoji(name="emoji", id=emoji_id)
            raise commands.BadArgument()


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

    @emoji.command(name="get", description=EmojiMess.get_emoji_brief)
    async def get_emoji(self, inter: discord.Interaction, emoji: PartialEmojiTransformer):
        """Get emoji in full size"""
        await inter.response.send_message(content=emoji.url)

    @has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True)
    @app_commands.command(name="add_server_emoji", description=EmojiMess.add_server_emoji_brief)
    async def add_emoji(self, inter: discord.Interaction, emoji: PartialEmojiTransformer, emoji_name: str = None):
        """Add emoji to server"""
        async with self.bot.morpheus_session.get(emoji.url) as resp:
            if resp.status == 200:
                image_bytes = await resp.read()
            else:
                await inter.response.send_message(content=EmojiMess.emoji_download_err)
                return

        if emoji_name:
            emoji.name = emoji_name

        new_emoji = await inter.guild.create_custom_emoji(name=emoji.name, image=image_bytes)
        await inter.response.send_message(content=EmojiMess.emoji_add_success(emoji=new_emoji))

    @tasks.loop(time=time(5, 0, tzinfo=get_local_zone()))
    async def download_emojis_task(self):
        await self.download_emojis(self.base_guild)

    @get_emoji.error
    @add_emoji.error
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.TransformerError) and error.transformer.annotation == PartialEmojiTransformer:
            await interaction.response.send_message(EmojiMess.invalid_emoji, ephemeral=True)
            return True
