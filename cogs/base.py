"""
Base cog class. All cogs should inherit from this class.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import discord

from config.app_config import config, load_config

if TYPE_CHECKING:
    from morpheus import Morpheus


class Base:
    bot: Morpheus
    config = config

    def __init__(self):
        self.tasks = []

    @cached_property
    def base_guild(self) -> discord.TextChannel:
        return self.bot.get_guild(Base.config.guild_id)

    @cached_property
    def bot_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.config.bot_channel)

    @cached_property
    def bot_dev_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.config.bot_dev_channel)

    @cached_property
    def gay_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.config.gay_channel)

    @cached_property
    def nasa_channels(self) -> list[discord.TextChannel]:
        return [self.bot.get_channel(channel) for channel in self.config.nasa_channels]

    @cached_property
    def xkcd_channels(self) -> list[discord.TextChannel]:
        return [self.bot.get_channel(channel) for channel in self.config.xkcd_channels]

    def cog_unload(self) -> None:
        for task in self.tasks:
            task.cancel()

    def cog_load(self) -> None:
        load_config()
