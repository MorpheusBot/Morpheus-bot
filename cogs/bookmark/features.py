from __future__ import annotations

import re
from typing import TYPE_CHECKING

import discord

from utils.constants import MAX_FILE_SIZE
from utils.general import split_to_parts

from .messages import BookmarkMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class BookmarkFeatures:
    def __init__(self, bot):
        self.bot = bot

    async def create_image_embed(
        self, ctx: discord.Interaction | BookmarkContext, image, title_name=None
    ) -> discord.Embed:
        """Create embed from image only"""
        if not title_name:
            title_name = BookmarkMess.bookmark_title(server=ctx.guild.name)

        author = ctx.message.author
        embed = discord.Embed(title=title_name, color=author.color)
        embed.set_author(name=author, icon_url=author.display_avatar.url)
        embed.set_image(image)
        embed.add_field(name="Channel", value=f"{ctx.message.channel.mention} - #{ctx.message.channel}")
        return embed

    async def create_bookmark_embed(self, ctx: discord.Interaction | BookmarkContext, title_name=None):
        if not title_name:
            title_name = BookmarkMess.bookmark_title(server=ctx.guild.name)

        author = ctx.message.author
        embed = discord.Embed(title=title_name, color=author.color)
        embed.set_author(name=author, icon_url=author.display_avatar.url)

        content = ""
        if ctx.message.embeds:
            for embed in ctx.message.embeds:
                embed.title, embed.color = title_name, author.color
                embed.set_author(name=author, icon_url=author.display_avatar.url)

        if ctx.message.content:
            content = ctx.message.content
        else:
            content += "*Empty*"

        # create list of attachments
        upload_limit = False
        images = []
        files_attached = []
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if attachment.size > MAX_FILE_SIZE:  # max size bot is able to send to dm
                    upload_limit = True
                    continue
                if re.search(r"\.png|\.jpg|\.jpeg|\.gif$", str(attachment)):
                    images.append(attachment)
                else:
                    files_attached.append(await attachment.to_file())

        if images:
            embed.set_image(images[0])
            del images[0]

        if ctx.message.stickers:
            for sticker in ctx.message.stickers:
                files_attached.append(await sticker.to_file())

        if len(content) > 1024:
            parts = split_to_parts(content, 1024)
            for msg in parts:
                embed.add_field(name="Původní zpráva", value=msg, inline=False)
        else:
            embed.add_field(name="Původní zpráva", value=content, inline=False)

        if upload_limit:
            embed.add_field(name="Poznámka", value=BookmarkMess.bookmark_upload_limit, inline=False)
        embed.add_field(name="Channel", value=f"{ctx.message.channel.mention} - #{ctx.message.channel}")
        return ([embed], images, files_attached)


class BookmarkContext:
    """
    Represents the context of a bookmarked message.

    Parameters
    ----------
    bot : Morpheus
        The instance of the bot.
    payload : discord.RawReactionActionEvent
        The payload of the reaction event.
    channel_id : int
        The ID of the channel where the bookmarked message is located.
    message_id : int
        The ID of the bookmarked message.
    guild_id : int
        The ID of the guild where the bookmarked message is located.
    member : discord.Member
        The member who reacted to the bookmarked message.
    message : discord.Message
        The bookmarked message.
    channel : discord.TextChannel
        The channel where the bookmarked message is located.
    guild : discord.Guild
        The guild where the bookmarked message is located.
    """

    def __init__(self, bot: Morpheus, payload: discord.RawReactionActionEvent):
        self.bot = bot
        self.channel_id = payload.channel_id
        self.message_id = payload.message_id
        self.guild_id = payload.guild_id
        self.member = payload.member
        self.message = None
        self.channel = None
        self.guild = None

    async def get_context(self):
        """
        Retrieves the context of the bookmarked message.

        This method fetches the channel, message, and guild associated with the bookmarked message.
        """
        self.channel = self.bot.get_channel(self.channel_id)
        self.message = await self.channel.fetch_message(self.message_id)
        self.guild = self.bot.get_guild(self.guild_id)
