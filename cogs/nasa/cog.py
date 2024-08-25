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

from .features import create_nasa_embed, nasa_daily_image
from .messages import NasaMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Nasa(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.send_nasa_image.start()]
        self.check = room_check.RoomCheck(bot)

    @default_cooldown()
    @app_commands.command(name="nasa_daily_image", description=NasaMess.nasa_image_brief)
    async def nasa_image(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        response = await nasa_daily_image(self.bot.morpheus_session, self.config.nasa_token)
        embed, video = await create_nasa_embed(inter.user, response)
        await inter.edit_original_response(embed=embed)
        if video:
            await inter.followup.send(video)

    @tasks.loop(time=time(7, 0, tzinfo=get_local_zone()))
    async def send_nasa_image(self):
        response = await nasa_daily_image(self.bot.morpheus_session, self.config.nasa_token)
        embed, video = await create_nasa_embed(self.bot.user, response)
        for channel in self.nasa_channels:
            await channel.send(embed=embed)
            if video:
                await channel.send(video)
