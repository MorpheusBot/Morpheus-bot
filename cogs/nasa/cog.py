"""
Cog for sending name days and birthdays.
"""

from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.base import Base
from custom import room_check
from custom.cooldowns import default_cooldown
from utils.general import get_local_zone

from .features import create_nasa_embed, filename, get_nasa_image, nasa_daily_image
from .messages import NasaMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Nasa(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.send_nasa_image.start(), self.download_nasa_image.start()]
        self.check = room_check.RoomCheck(bot)

    @default_cooldown()
    @app_commands.command(name="nasa_daily_image", description=NasaMess.nasa_image_brief)
    async def nasa_image(self, inter: discord.Interaction):
        ephemeral = self.check.botroom_check(inter)
        await inter.response.defer(ephemeral=ephemeral)

        response = await nasa_daily_image(self.bot.morpheus_session)
        embed, attachment = await create_nasa_embed(inter.user, response)
        if attachment:
            await inter.followup.send(embed=embed)
            await inter.followup.send(content=attachment, ephemeral=ephemeral)
        else:
            await inter.followup.send(embed=embed, file=discord.File(filename))

    @tasks.loop(time=time(7, 0, tzinfo=get_local_zone()))
    async def send_nasa_image(self):
        response = await nasa_daily_image(self.bot.morpheus_session)
        await get_nasa_image(self.bot.morpheus_session, response)
        embed, attachment = await create_nasa_embed(self.bot.user, response)
        for channel in self.nasa_channels:
            if attachment:
                await channel.send(embed=embed)
                await channel.send(content=attachment)
            else:
                await channel.send(embed=embed, file=discord.File(filename))

    @tasks.loop(count=1)
    async def download_nasa_image(self):
        response = await nasa_daily_image(self.bot.morpheus_session, self.config.nasa_token)
        await get_nasa_image(self.bot.morpheus_session, response)
