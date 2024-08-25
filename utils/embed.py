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


class ViewRowFull(Exception):
    """Adding a Item to already filled row"""

    pass


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
        roll_arroud: bool = True,
        end_arrow: bool = True,
        timeout: int = 300,
        page: int = 1,
        show_page: bool = False,
    ):
        """Embed pagination view

        param: discord.User author: command author, used for locking pagination
        param: List[discord.Embed] embeds: List of embed to be paginated
        param int row: On which row should be buttons added, defaults to first
        param bool perma_lock: If true allow just message author to change pages, without dynamic lock button
        param bool roll_arroud: After last page rollaround to first
        param bool end_arrow: If true use also '⏩' button
        param int timeout: Seconds until disabling interaction, use None for always enabled
        param int page: Starting page
        param bool show_page: Show page number at the bottom of embed, e.g.: 2/4
        """
        self.page = page
        self.author = author
        self.locked = False
        self.roll_arroud = roll_arroud
        self.perma_lock = perma_lock
        self.max_page = len(embeds)
        self.embeds = embeds
        self.message: discord.Message
        super().__init__(timeout=timeout)
        if self.max_page <= 1:
            return
        if show_page:
            self.add_page_numbers()

        self.add_item(
            PaginationButton(emoji="⏪", custom_id="embed:start_page", row=row, style=discord.ButtonStyle.primary)
        )
        self.add_item(
            PaginationButton(emoji="◀", custom_id="embed:prev_page", row=row, style=discord.ButtonStyle.primary)
        )
        self.add_item(
            PaginationButton(emoji="▶", custom_id="embed:next_page", row=row, style=discord.ButtonStyle.primary)
        )
        if end_arrow:
            self.add_item(
                PaginationButton(emoji="⏩", custom_id="embed:end_page", row=row, style=discord.ButtonStyle.primary)
            )
        if not perma_lock:
            # if permanent lock is applied, dynamic lock is removed from buttons
            self.lock_button = PaginationButton(
                emoji="🔓", custom_id="embed:lock", row=0, style=discord.ButtonStyle.success
            )
            self.add_item(self.lock_button)

    @property
    def embed(self):
        return self.embeds[self.page - 1]

    @embed.setter
    def embed(self, value):
        self.embeds[self.page - 1] = value

    def add_item(self, item: discord.ui.Item) -> None:
        row_cnt = 0
        for child in self.children:
            if item.emoji == child.emoji:
                child.disabled = False
                return
            if item.row == child.row:
                row_cnt += 1
        if row_cnt >= 5:
            # we are trying to add new button to already filled row
            raise ViewRowFull
        super().add_item(item)

    def add_page_numbers(self):
        """Set footers with page numbers for each embed in list"""
        for page, embed in enumerate(self.embeds):
            add_author_footer(embed, self.author, additional_text=[f"Page {page+1}/{self.max_page}"])

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

    async def interaction_check(self, inter: discord.Interaction) -> bool | None:
        if inter.data["custom_id"] == "embed:lock":
            if inter.user.id == self.author.id:
                self.locked = not self.locked
                if self.locked:
                    self.lock_button.style = discord.ButtonStyle.danger
                    self.lock_button.emoji = "🔒"
                else:
                    self.lock_button.style = discord.ButtonStyle.success
                    self.lock_button.emoji = "🔓"
                await inter.response.edit_message(view=self)
            else:
                await inter.response.send(GlobalMessages.embed_not_author, ephemeral=True)
            return False
        ids = ["embed:start_page", "embed:prev_page", "embed:next_page", "embed:end_page"]
        if inter.data["custom_id"] not in ids or self.max_page <= 1:
            return False
        if (self.perma_lock or self.locked) and inter.user.id != self.author.id:
            await inter.response.send(GlobalMessages.embed_not_author, ephemeral=True)
            return False
        self.page = self.pagination_next(inter.data["custom_id"], self.page, self.max_page, self.roll_arroud)
        await inter.response.edit_message(embed=self.embed)
        return True

    async def on_timeout(self):
        await self.message.edit(view=None)
