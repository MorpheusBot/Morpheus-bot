"""
Cog for sending name days and birthdays.
"""

from __future__ import annotations

import asyncio
from datetime import date, time
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

import utils.utils as utils
from cogs.base import Base
from custom import room_check
from custom.cooldowns import default_cooldown

from .messages import NameDayMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class NameDay(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.send_names.start()]
        self._owner_id = bot.owner_id
        self.check = room_check.RoomCheck(bot)

    async def _name_day_cz(self):
        try:
            url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
            async with self.bot.morpheus_session.get(url) as resp:
                res = await resp.json()
            names = []
            for i in res:
                names.append(i["name"])
            return NameDayMess.name_day_cz(name=", ".join(names))
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
            return "Website unreachable"

    async def _name_day_sk(self):
        try:
            url = f"http://svatky.adresa.info/json?lang=sk&date={date.today().strftime('%d%m')}"
            async with self.bot.morpheus_session.get(url) as resp:
                res = await resp.json()
            names = []
            for i in res:
                names.append(i["name"])
            return NameDayMess.name_day_sk(name=", ".join(names))
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
            return "Website unreachable"

    @default_cooldown()
    @app_commands.command(name="svatek", description=NameDayMess.name_day_cz_brief)
    async def name_day_cz(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        name_day_cz = await self._name_day_cz()
        await inter.edit_original_response(content=name_day_cz)

    @default_cooldown()
    @app_commands.command(name="meniny", description=NameDayMess.name_day_sk_brief)
    async def name_day_sk(self, inter: discord.Interaction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        name_day_sk = await self._name_day_sk()
        await inter.edit_original_response(content=name_day_sk)

    @tasks.loop(time=time(6, 0, tzinfo=utils.get_local_zone()))
    async def send_names(self):
        name_day_cz = await self._name_day_cz()
        name_day_sk = await self._name_day_sk()
        mentions = discord.AllowedMentions.none()
        for channel in self.config.name_day_channels:
            channel = self.bot.get_channel(channel)
            await channel.send(f"{name_day_cz}\n{name_day_sk}", allowed_mentions=mentions)
