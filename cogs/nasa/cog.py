"""
Cog for sending name days and birthdays.
"""

from __future__ import annotations

import asyncio
from datetime import time
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

import utils.utils as utils
from cogs.base import Base
from custom import room_check
from custom.cooldowns import default_cooldown
from custom.custom_errors import ApiError

from .features import create_nasa_embed
from .messages import NasaMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Nasa(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.send_nasa_image.start()]
        self.check = room_check.RoomCheck(bot)

    async def nasa_daily_image(self) -> dict:
        try:
            url = f"https://api.nasa.gov/planetary/apod?api_key={self.config.nasa_key}&concept_tags=True"
            async with self.bot.morpheus_session.get(url) as resp:
                response = await resp.json()
            return response
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
            raise ApiError(error=str(error))

    @default_cooldown()
    @app_commands.command(name="nasa_daily_image", description=NasaMess.nasa_image_brief)
    async def nasa_image(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        response = await self.nasa_daily_image()
        embed, video = create_nasa_embed(response)
        await inter.edit_original_response(embed=embed)
        if video:
            await inter.followup.send(video)

    @tasks.loop(time=time(6, 0, tzinfo=utils.get_local_zone()))
    async def send_nasa_image(self):
        response = await self.nasa_daily_image()
        embed, video = create_nasa_embed(response)
        for channel in self.nasa_channels:
            await channel.send(embed=embed)
            if video:
                await channel.send(video)
