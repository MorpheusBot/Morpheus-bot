from __future__ import annotations

import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import default_cooldown
from database.guild import GuildDB, GuildPhraseDB
from utils.general import cut_string_by_words

from .messages import GuildConfigMess

if TYPE_CHECKING:
    from morpheus import Morpheus


async def autocomp_replies(inter: discord.Interaction, user_input: str) -> list[app_commands.Choice[str]]:
    user_input = user_input.lower()
    phrases = await GuildDB.get_phrases(str(inter.guild.id))
    return [
        app_commands.Choice(name=phrase, value=phrase) for phrase in phrases.keys() if user_input in phrase.lower()
    ][:10]


@app_commands.guild_only()
@default_cooldown()
class ReplyGroup(app_commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GuildConfig(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.phrases = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            guild_db = await GuildDB.get_guild(str(guild.id))
            if not guild_db:
                guild_db = await GuildDB.add_guild(str(guild.id))
            self.phrases[guild.id] = guild_db.phrases_dict

    reply_group = ReplyGroup(name="reply", description="Autoreply commands")

    @commands.has_permissions(administrator=True)
    @app_commands.guild_only()
    @default_cooldown()
    @app_commands.command(name="edit_config", description=GuildConfigMess.edit_config_brief)
    async def edit_config(self, inter: discord.Interaction, info_channel: discord.TextChannel):
        """for now only info channel in future all attributes guild config can have"""
        guild_db = await GuildDB.get_guild(str(inter.guild.id))
        await guild_db.set_info_channel(info_channel.id)
        await inter.response.send_message(GuildConfigMess.info_channel_set(info_channel=info_channel.mention))

    @commands.Cog.listener("on_message")
    async def reply(self, message: discord.Message):
        """sends messages to users depending on the content"""
        if message.guild is None:
            return

        if message.author.bot:
            return
        elif "uh oh" in message.content:
            await message.channel.send("uh oh")
        elif f"<@!{self.bot.user.id}>" in message.content or f"<@{self.bot.user.id}>" in message.content:
            await message.channel.send(random.choice(GuildConfigMess.Morpheus))
        else:
            phrases = self.phrases.get(message.guild.id)
            if not phrases:
                return
            for key, value in phrases.items():
                if key.lower() == message.content.lower():
                    await message.channel.send(value)

    @reply_group.command(name="add", description=GuildConfigMess.add_reply_brief)
    async def add_reply(self, inter: discord.Interaction, key: str, reply: str):
        phrase = await GuildPhraseDB.add_phrase(str(inter.guild.id), key, reply)
        if not phrase:
            await inter.response.send_message(GuildConfigMess.reply_exists(key=key))
            return

        self.phrases[inter.guild.id] = await GuildDB.get_phrases(str(inter.guild.id))
        await inter.response.send_message(GuildConfigMess.reply_added(key=key))

    @reply_group.command(name="remove", description=GuildConfigMess.rem_reply_brief)
    @app_commands.autocomplete(key=autocomp_replies)
    async def remove_reply(self, inter: discord.Interaction, key: str):
        phrase = await GuildPhraseDB.remove_phrase(str(inter.guild.id), key)
        if not phrase:
            await inter.response.send_message(GuildConfigMess.reply_not_found(key=key))
            return

        self.phrases[inter.guild.id] = await GuildDB.get_phrases(str(inter.guild.id))
        await inter.response.send_message(GuildConfigMess.reply_removed(key=key))

    @reply_group.command(name="list", description=GuildConfigMess.list_reply_brief)
    async def list_reply(self, inter: discord.Interaction):
        phrases = await GuildDB.get_phrases(str(inter.guild.id))
        if not phrases:
            await inter.response.send_message(GuildConfigMess.no_replies)
            return

        blue_c = "\u001b[2;34m"
        pink_c = "\u001b[2;35m"
        default_c = "\u001b[0m"
        replies_list = [f"{blue_c}{key}{default_c}: {pink_c}{value}{default_c}\n" for key, value in phrases.items()]
        replies_str = "".join(replies_list)
        replies = cut_string_by_words(replies_str, 1800, "\n")
        await inter.response.send_message(f"{GuildConfigMess.reply_list}```ansi\n{replies[0]}```")
        for reply in replies[1:]:
            await inter.followup.send(f"```ansi\n{reply}```")
