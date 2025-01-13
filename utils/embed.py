from __future__ import annotations

import platform
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Iterable

import discord

from config.messages import GlobalMessages

from .general import get_commands_count

if TYPE_CHECKING:
    from morpheus import Morpheus


def info_embed(bot: Morpheus) -> discord.Embed:
    embed = discord.Embed(title="Morpheus", url=GlobalMessages.morpheus_url, color=discord.Colour.yellow())
    embed.add_field(name="ID", value=bot.user.id, inline=False)
    embed.add_field(name="Python", value=platform.python_version())
    embed.add_field(name="Discordpy", value=discord.__version__)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)} ms")
    embed.add_field(name="Guilds", value=len(bot.guilds))

    commands = get_commands_count(bot)
    commands = GlobalMessages.commands_count(
        sum=commands.get("sum", "Missing"),
        context=commands.get("context", "Missing"),
        slash=commands.get("slash", "Missing"),
        message=commands.get("message", "Missing"),
        user=commands.get("user", "Missing"),
    )
    embed.add_field(name="Commands", value=commands, inline=False)
    embed.set_thumbnail(url=bot.user.avatar.url)
    return embed


def add_author_footer(
    embed: discord.Embed,
    author: discord.User,
    set_timestamp=True,
    additional_text: Iterable[str] = [],
    anonymous: bool = False,
):
    """
    Adds footer to the embed with author name and icon from ctx.

    :param author: author info
    :param embed: discord.Embed object
    :param set_timestamp: bool, should the embed's timestamp be set
    :param additional_text: Iterable of strings that will be joined with author name by pipe symbol, eg.:
    :param anonymous: bool, show author as Anonymous
    "john#2121 | text1 | text2" or "Anonymous | text1 | text2"
    """

    if set_timestamp:
        embed.timestamp = datetime.now(tz=timezone.utc)

    if anonymous:
        display_name = "Anonymous"
        display_avatar = author.default_avatar.url
    else:
        display_name = author.display_name
        display_avatar = author.display_avatar.url

    embed.set_footer(icon_url=display_avatar, text=" | ".join((str(display_name), *additional_text)))


class PaginationButton(discord.ui.Button):
    """Subclass of discord.ui.Button with custom callback.

    Everything is handled in View's interaction_check method. No need for callback.
    """

    def __init__(self, emoji, custom_id, row, style, **kwargs):
        super().__init__(emoji=emoji, custom_id=custom_id, row=row, style=style, **kwargs)

    async def callback(self, interaction: discord.Interaction): ...


class PaginationView(discord.ui.View):
    def __init__(
        self,
        author: discord.User,
        embeds: list[discord.Embed],
        row: int = 0,
        perma_lock: bool = False,
        roll_around: bool = True,
        end_arrow: bool = True,
        timeout: int = 300,
        page: int = 1,
        show_page: bool = False,
    ):
        """Embed pagination view

        param discord.User author: command author, used for locking pagination
        param List[discord.Embed] embeds: List of embed to be paginated
        param int row: On which row should be buttons added, defaults to first
        param bool perma_lock: If true allow just message author to change pages, without dynamic lock button
        param bool roll_around: After last page rollaround to first
        param bool end_arrow: If true use also '⏩' button
        param int timeout: Seconds until disabling interaction, use None for always enabled
        param int page: Starting page
        param bool show_page: Show page number at the bottom of embed, e.g.: 2/4
        """
        super().__init__(timeout=timeout)
        self.author = author
        self.embeds = embeds
        self.perma_lock = perma_lock
        self.roll_around = roll_around
        self.page = page
        self.max_page = len(embeds)
        self.locked = False
        self.dynam_lock = False
        self.message: discord.Message

        if self.max_page <= 1:
            return  # No need for pagination

        if show_page:
            self.add_page_numbers()

        # Add all buttons to the view and set their callbacks
        self.start_button = discord.ui.Button(
            emoji="⏪", custom_id="embed:start", row=row, style=discord.ButtonStyle.primary
        )
        self.start_button.callback = self.start_callback
        self.add_item(self.start_button)

        self.prev_button = discord.ui.Button(
            emoji="◀", custom_id="embed:prev", row=row, style=discord.ButtonStyle.primary
        )
        self.prev_button.callback = self.prev_callback
        self.add_item(self.prev_button)

        self.next_button = discord.ui.Button(
            emoji="▶", custom_id="embed:next", row=row, style=discord.ButtonStyle.primary
        )
        self.next_button.callback = self.next_callback
        self.add_item(self.next_button)

        if end_arrow:
            self.end_button = discord.ui.Button(
                emoji="⏩", custom_id="embed:end", row=row, style=discord.ButtonStyle.primary
            )
            self.end_button.callback = self.end_callback
            self.add_item(self.end_button)

        if not self.perma_lock:
            # if permanent lock is not applied, dynamic lock is added
            self.lock_button = discord.ui.Button(
                emoji="🔓", custom_id="embed:lock", row=row, style=discord.ButtonStyle.success
            )
            self.lock_button.callback = self.lock_callback
            self.add_item(self.lock_button)

    @property
    def embed(self):
        return self.embeds[self.page - 1]

    @embed.setter
    def embed(self, value):
        self.embeds[self.page - 1] = value

    def add_page_numbers(self):
        """Set footers with page numbers for each embed in list"""
        for page, embed in enumerate(self.embeds):
            add_author_footer(embed, self.author, additional_text=[f"Page {page + 1}/{self.max_page}"])

    def pagination_next(self, id: str, page: int, max_page: int, roll_around: bool = True) -> int:
        if "next" in id:
            next_page = page + 1
        elif "prev" in id:
            next_page = page - 1
        elif "start" in id:
            next_page = 1
        elif "end" in id:
            next_page = max_page
        if 1 <= next_page <= max_page:
            return next_page
        elif roll_around and next_page == 0:
            return max_page
        elif roll_around and next_page > max_page:
            return 1
        else:
            return 0

    async def lock_callback(self, interaction: discord.Interaction):
        self.dynam_lock = not self.dynam_lock
        if self.dynam_lock:
            self.lock_button.style = discord.ButtonStyle.danger
            self.lock_button.emoji = "🔒"
        else:
            self.lock_button.style = discord.ButtonStyle.success
            self.lock_button.emoji = "🔓"
        await interaction.response.edit_message(view=self)

    async def start_callback(self, interaction: discord.Interaction):
        await self.pagination_callback(interaction, "start")

    async def prev_callback(self, interaction: discord.Interaction):
        await self.pagination_callback(interaction, "prev")

    async def next_callback(self, interaction: discord.Interaction):
        await self.pagination_callback(interaction, "next")

    async def end_callback(self, interaction: discord.Interaction):
        await self.pagination_callback(interaction, "end")

    async def pagination_callback(self, interaction: discord.Interaction, id: str):
        self.page = self.pagination_next(id, self.page, self.max_page, self.roll_around)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def interaction_check(self, inter: discord.Interaction) -> bool | None:
        if (self.perma_lock or self.dynam_lock) and inter.user.id != self.author.id:
            """Message has permanent lock or dynamic lock enabled"""
            await inter.response.send_message(GlobalMessages.embed_not_author, ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        await self.message.edit(view=None)
