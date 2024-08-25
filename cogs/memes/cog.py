from __future__ import annotations

import asyncio
from functools import cached_property
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import custom_cooldown, default_cooldown
from utils.user import get_or_fetch_user

from .messages import MemesMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Memes(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot

    @cached_property
    def jany(self) -> discord.User:
        return get_or_fetch_user(self.bot, Base.config.jany)

    @cached_property
    def ilbinek(self) -> discord.User:
        return get_or_fetch_user(self.bot, Base.config.ilbinek)

    @default_cooldown()
    @app_commands.command(name="drzpicu", description=MemesMess.drzpicu_brief)
    async def drzpicu(self, inter: discord.Interaction, user: discord.User = None):
        if user is None:
            user = self.ilbinek
        await inter.response.send_message(f"drz picu {user.mention}")

    @default_cooldown()
    @app_commands.command(name="nebudsalty", description=MemesMess.nebudsalty_brief)
    async def nebudsalty(self, inter: discord.Interaction, user: discord.User = None):
        if user is None:
            user = self.jany
        await inter.response.send_message(f":salt: nebud salty {user.mention}")

    @app_commands.guild_only()
    @default_cooldown()
    @app_commands.command(name="nickname", description=MemesMess.nickname_brief)
    async def nickname(
        self,
        inter: discord.Interaction,
        target: discord.Member,
        nickname: app_commands.Range[str, 0, 32] = None,
    ):
        try:
            await target.edit(nick=nickname)
        except discord.errors.Forbidden:
            await inter.response.send_message(MemesMess.cant_change_nickname)
        else:
            await inter.response.send_message(MemesMess.nickname_success)

    @custom_cooldown(rate=1, per=100.0)
    @commands.command(hidden=True)
    async def tagrage(self, ctx: commands.Context, user: discord.Member, *text):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        for x in range(5):
            await ctx.send(f"{user.mention} {' '.join(text)}")
            await asyncio.sleep(5)
