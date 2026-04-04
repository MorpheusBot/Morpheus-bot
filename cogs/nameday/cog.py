"""
Cog for sending name days and birthdays.
"""

from __future__ import annotations

import json
from datetime import datetime, time
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.base import Base
from custom import room_check
from custom.cooldowns import default_cooldown
from utils.general import get_local_zone

from . import features
from .messages import NameDayMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class NameDay(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.send_names.start()]
        self.check = room_check.RoomCheck(bot)

        # Load namedays data
        namedays_path = Path(__file__).parent / "namedays.json"
        with open(namedays_path, "r", encoding="utf-8") as f:
            self.namedays = json.load(f)

        # Create reverse indexes for efficient name lookups
        self.cz_name_index, self.sk_name_index = features.build_name_indexes(self.namedays)

    async def _autocomplete_name(
        self,
        inter: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for Czech and Slovak names based on command."""
        if inter.command.name == "svatek":
            return features.autocomplete_name(self.cz_name_index, current)
        else:  # meniny
            return features.autocomplete_name(self.sk_name_index, current)

    async def _handle_nameday_command(
        self,
        inter: discord.Interaction,
        name: str | None,
        locale: str,
        name_index: dict[str, list[str]],
        name_found_msg: str,
        name_not_found_msg: str,
    ):
        """Common logic for nameday commands.

        Args:
            inter: Discord interaction
            name: Name to search for (None for today's nameday)
            locale: Locale code ("cz" or "sk")
            name_index: Name index for the locale
            name_found_msg: Message template for when name is found
            name_not_found_msg: Message template for when name is not found
        """
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))

        if name is None:
            # Return today's nameday
            response = features.get_name_day(self.namedays, locale)
        else:
            # Search by name
            dates = features.search_name(name_index, name)
            if dates:
                formatted_dates = [datetime.strptime(d, "%m-%d").strftime("%d.%m.") for d in dates]
                response = name_found_msg.format(name=name.capitalize(), dates=", ".join(formatted_dates))
            else:
                response = name_not_found_msg.format(name=name.capitalize())

        await inter.edit_original_response(content=response)

    @default_cooldown()
    @app_commands.command(name="svatek", description=NameDayMess.name_day_cz_brief)
    @app_commands.describe(name=NameDayMess.name_day_cz_param)
    @app_commands.autocomplete(name=_autocomplete_name)
    async def name_day_cz(
        self,
        inter: discord.Interaction,
        name: str | None = None,
    ):
        await self._handle_nameday_command(
            inter,
            name,
            "cz",
            self.cz_name_index,
            NameDayMess.name_found_cz,
            NameDayMess.name_not_found_cz,
        )

    @default_cooldown()
    @app_commands.command(name="meniny", description=NameDayMess.name_day_sk_brief)
    @app_commands.describe(name=NameDayMess.name_day_sk_param)
    @app_commands.autocomplete(name=_autocomplete_name)
    async def name_day_sk(
        self,
        inter: discord.Interaction,
        name: str | None = None,
    ):
        await self._handle_nameday_command(
            inter,
            name,
            "sk",
            self.sk_name_index,
            NameDayMess.name_found_sk,
            NameDayMess.name_not_found_sk,
        )

    @tasks.loop(time=time(6, 0, tzinfo=get_local_zone()))
    async def send_names(self):
        name_day_cz = features.get_name_day(self.namedays, "cz")
        name_day_sk = features.get_name_day(self.namedays, "sk")
        mentions = discord.AllowedMentions.none()
        message = NameDayMess.daily_format.format(cz=name_day_cz, sk=name_day_sk)
        for channel in self.config.name_day_channels:
            channel = self.bot.get_channel(channel)
            await channel.send(message, allowed_mentions=mentions)
