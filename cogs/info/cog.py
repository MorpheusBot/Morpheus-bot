from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import default_cooldown
from custom.enums import DiscordTimestamps
from database.guild import GuildDB
from utils.embed import add_author_footer

from . import features as info_features
from .messages import InfoMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Info(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        info_channel_id = await GuildDB.get_info_channel(member.guild.id)
        if not info_channel_id:
            return
        channel = self.bot.get_channel(int(info_channel_id))
        await channel.send(InfoMess.welcome_user(member.mention))

    @app_commands.guild_only()
    @default_cooldown()
    @app_commands.command(name="user_info", description=InfoMess.user_info_brief)
    async def user_info(self, inter: discord.Interaction, user: discord.Member = None):
        user = user or inter.user
        user = inter.guild.get_member(user.id)
        style = DiscordTimestamps.ShortDateTime.value

        embed = discord.Embed(title=f"{user.display_name} ({user.name})", color=user.color)
        add_author_footer(embed, inter.user)

        if user.avatar is not None:
            embed.set_thumbnail(url=user.avatar)

        embed.add_field(name="Status", value=str(user.status).title(), inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)

        if user.roles[1:]:
            roles = " ".join([role.mention for role in user.roles[1:][::-1]])
            embed.add_field(name="Roles", value=roles, inline=False)

        embed.add_field(
            name="Created account", value=discord.utils.format_dt(user.created_at, style=style), inline=True
        )

        if user.joined_at is not None:
            joined_server = discord.utils.format_dt(user.joined_at, style=style)
            embed.add_field(name="Joined server", value=joined_server, inline=True)
        if user.premium_since is not None:
            boosted = discord.utils.format_dt(user.premium_since, style=style)
            embed.add_field(name="Boosted", value=boosted, inline=True)

        await inter.response.send_message(embed=embed)

    @default_cooldown()
    @app_commands.command(name="guild_info", description=InfoMess.guild_info_brief)
    async def guild_info(self, inter: discord.Interaction):
        await inter.response.defer()
        embed = discord.Embed(
            title=inter.guild.name, colour=inter.guild.owner.colour, description=inter.guild.description
        )
        add_author_footer(embed, inter.user)
        style = DiscordTimestamps.ShortDateTime.value

        if inter.guild.icon is not None:
            embed.set_thumbnail(url=inter.guild.icon)

        embed.add_field(name="Owner", value=inter.guild.owner.mention, inline=True)
        embed.add_field(
            name="Created at", value=discord.utils.format_dt(inter.guild.created_at, style=style), inline=True
        )
        embed.add_field(name="Members", value=inter.guild.member_count, inline=True)
        embed.add_field(name="Bots", value=len([member for member in inter.guild.members if member.bot]), inline=True)
        try:
            embed.add_field(
                name="Banned users",
                value=len([entry async for entry in inter.guild.bans(limit=None)]),
                inline=False,
            )
        except discord.Forbidden:
            embed.add_field(name="Banned users", value=InfoMess.missing_permission, inline=False)

        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Categories", value=len(inter.guild.categories), inline=True)
        embed.add_field(name="Text channels", value=len(inter.guild.text_channels), inline=True)
        embed.add_field(name="Threads", value=len(inter.guild.threads), inline=True)
        embed.add_field(name="Voice channels", value=len(inter.guild.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(inter.guild.roles), inline=True)
        try:
            embed.add_field(name="Active invites", value=len(await inter.guild.invites()), inline=True)
        except discord.Forbidden:
            embed.add_field(name="Active invites", value=InfoMess.missing_permission, inline=True)

        embed.add_field(name="Guild level", value=inter.guild.premium_tier, inline=True)
        embed.add_field(name="Boosters", value=inter.guild.premium_subscription_count, inline=True)

        emojis, animated_emojis = info_features.get_emoji_count(inter.guild)
        embed.add_field(name="Emojis count/max", value=f"{emojis}/{inter.guild.emoji_limit}", inline=True)
        embed.add_field(name="Animated emojis", value=f"{animated_emojis}/{inter.guild.emoji_limit}", inline=True)

        await inter.edit_original_response(embed=embed)
