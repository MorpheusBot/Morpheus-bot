from __future__ import annotations

import logging
import traceback
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom import custom_errors
from custom.enums import DiscordTimestamps
from utils.general import cut_string
from utils.interaction import custom_send

from .messages import ErrorMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Error(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot

    def cog_load(self):
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = self._old_tree_error

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, custom_errors.NotAdminError):
            await ctx.reply(error.message)
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(ErrorMess.not_enough_perms)
            return

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.now() + timedelta(seconds=error.retry_after)
            retry_after = discord.utils.format_dt(time, style=DiscordTimestamps.RelativeTime.value)
            await ctx.reply(ErrorMess.command_on_cooldown(time=retry_after))
            return

        if isinstance(error, commands.UserInputError):
            await ctx.reply(error)
            return

        if isinstance(error, custom_errors.ApiError):
            await ctx.reply(embed=error.embed)
            return

        if isinstance(error, custom_errors.InvalidTime):
            await ctx.reply(error.message)
            return

        channel = self.bot_dev_channel
        if channel is None:
            return

        message = await ctx.reply(ErrorMess.error_happened)

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logging.error(output)

        embed = discord.Embed(title=f"Ignoring exception on command {ctx.command}", color=0xFF0000)
        embed.add_field(name="Author", value=str(ctx.author))

        if ctx.guild and ctx.guild.id != Base.config.guild_id:
            embed.add_field(name="Guild", value=ctx.guild.name)
        embed.add_field(name="Zpráva", value=ctx.message.content[:1000], inline=False)
        embed.add_field(name="Link", value=ctx.message.jump_url, inline=False)

        await channel.send(embed=embed)

        output = cut_string(output, 1900)
        for message in output:
            await channel.send(f"```\n{message}\n```")

    async def on_app_command_error(self, inter: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, custom_errors.NotAdminError):
            await custom_send(inter, error.message, ephemeral=True)
            return

        if isinstance(error, custom_errors.ApiError):
            await custom_send(inter, embed=error.embed)
            return

        if isinstance(error, custom_errors.InvalidTime):
            await custom_send(inter, error.message, ephemeral=True)
            return

        if isinstance(error, app_commands.MissingPermissions):
            await custom_send(inter, ErrorMess.not_enough_perms, ephemeral=True)
            return

        if isinstance(error, app_commands.CommandOnCooldown):
            time = datetime.now() + timedelta(seconds=error.retry_after)
            retry_after = discord.utils.format_dt(time, style=DiscordTimestamps.RelativeTime.value)
            await custom_send(inter, ErrorMess.command_on_cooldown(time=retry_after), ephemeral=True)
            return

        channel = self.bot_dev_channel
        if channel is None:
            return

        await custom_send(inter, ErrorMess.error_happened, edit=False)

        url = f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}"

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logging.error(output)

        embed = discord.Embed(title=f"Ignoring exception on command `/{inter.command.name}`", color=0xFF0000)
        embed.add_field(name="Author", value=str(inter.user))

        guild = inter.guild if inter.guild else "DMs"
        embed.add_field(name="Guild", value=guild)

        options = inter.data.get("options", None)
        if options:
            options = [f"{item['name']}: {item['value']}" for item in options if item["type"] != 1]
            embed.add_field(name="Arguments", value="\n".join(options), inline=False)

        embed.add_field(name="Link", value=url, inline=False)

        await channel.send(embed=embed)

        output = cut_string(output, 1900)
        for message in output:
            await channel.send(f"```\n{message}\n```")

    @commands.Cog.listener()
    async def on_error(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        output = traceback.format_exc()
        logging.error(output)

        channel = self.bot_dev_channel
        if channel is None:
            return

        embeds = []
        guild = None
        for arg in args:
            if arg.guild_id:
                guild = self.bot.get_guild(arg.guild_id)
                event_guild = guild.name
                channel = guild.get_channel(arg.channel_id)
                message = await channel.fetch_message(arg.message_id)
                message = message.content[:1000]
            else:
                event_guild = "DM"
                message = arg.message_id

            user = self.bot.get_user(arg.user_id)
            if not user:
                user = arg.user_id
            else:
                channel = self.bot.get_channel(arg.channel_id)
                if channel:
                    message = await channel.fetch_message(arg.message_id)
                    if message.content:
                        message = message.content[:1000]
                    elif message.embeds:
                        embeds.extend(message.embeds)
                        message = "Embed v předchozí zprávě"
                    elif message.attachments:
                        message_out = ""
                        for attachment in message.attachments:
                            message_out += f"{attachment.url}\n"
                        message = message_out
                else:
                    message = arg.message_id
                user = str(user)
            embed = discord.Embed(title=f"Ignoring exception on event '{event}'", color=0xFF0000)
            embed.add_field(name="Message", value=message, inline=False)
            if arg.guild_id != Base.config.guild_id:
                embed.add_field(name="Guild", value=event_guild)

        output = cut_string(output, 1900)
        for embed in embeds:
            await channel.send(embed=embed)
        for message in output:
            await channel.send(f"```\n{message}```")
