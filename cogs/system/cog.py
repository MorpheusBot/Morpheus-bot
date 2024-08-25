from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import default_cooldown
from custom.permission_check import is_bot_admin
from utils.embed import info_embed

from . import features
from .buttons import SystemView
from .messages import SystemMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class System(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.unloadable_cogs = ["system"]

    @app_commands.check(is_bot_admin)
    @app_commands.command(name="shutdown", description=SystemMess.shutdown_brief)
    async def shutdown(self, inter: discord.Interaction):
        await inter.response.send_message("`Shutting down...`")
        await self.bot.morpheus_session.close()
        await self.bot.close()

    @app_commands.check(is_bot_admin)
    @app_commands.command(name="cogs", description=SystemMess.cogs_brief)
    async def cogs(self, inter: discord.Interaction):
        """
        Creates embed with button and select(s) to load/unload/reload cogs.

        Max number of cogs can be 100 (4x25).
        """
        await inter.response.defer()
        cog_chunks = await features.split_cogs()
        view = SystemView(self.bot, cog_chunks)
        embed = features.create_embed(self.bot)
        message = await inter.followup.send(embed=embed, view=view)

        # pass message object to classes
        view.message = message
        for i in range(len(cog_chunks)):
            view.selects[i].message = message

    @default_cooldown()
    @app_commands.command(name="morpheus", description=SystemMess.morpheus_brief)
    async def morpheus(self, inter: discord.Interaction):
        await inter.response.defer()
        embed = info_embed(self.bot)
        await inter.edit_original_response(embed=embed)

    @cogs.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
            await ctx.send(SystemMess.not_loaded.format(error.__cause__.name))
            return True
