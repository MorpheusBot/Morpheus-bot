"""
Cog containing commands that call random APIs for fun things.
"""

from __future__ import annotations

import asyncio
import random
import re
from datetime import time
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from cogs.base import Base
from custom.cooldowns import default_cooldown
from custom.custom_errors import ApiError
from utils.general import get_local_zone

from . import features
from .messages import FunMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Fun(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot
        self.tasks = [self.xkcd_daily.start()]
        self.xkcd_url: str = "https://xkcd.com"
        self.total_xkcd_posts: int = 0

    async def update_xkcd_posts(self):
        xkcd_post = await features.get_xkcd(self.bot.morpheus_session, f"{self.xkcd_url}/info.0.json")
        self.total_xkcd_posts = xkcd_post["num"]

    @default_cooldown()
    @app_commands.command(name="cat", description=FunMess.cat_brief)
    async def cat(self, inter: discord.InteractionMessage):
        """Get random image of a cat"""
        image_bytes, file_name = await features.get_image("https://api.thecatapi.com/v1/images/search")
        image_file = discord.File(image_bytes, filename=file_name)

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await self.get_fact("https://meowfacts.herokuapp.com/", "data")

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_footer(text=features.custom_footer(inter.user, "thecatapi.com"))
        embed.set_image(url=f"attachment://{file_name}")
        embeds: list[discord.Embed] = [embed]

        if fact_response:
            fact_embed = discord.Embed(
                title="Cat fact",
                description=fact_response,
                color=discord.Color.blue(),
            )
            fact_embed.set_footer(text=features.custom_footer(inter.user, "thecatapi.com"))
            embeds.append(fact_embed)

        await inter.response.send_message(file=image_file, embeds=embeds)

    @default_cooldown()
    @app_commands.command(name="dog", description=FunMess.dog_brief)
    async def dog(self, inter: discord.Interaction):
        """Get random image of a dog"""
        image_bytes, file_name = await features.get_image("https://api.thedogapi.com/v1/images/search")
        image_file = discord.File(image_bytes, filename=file_name)

        fact_response: str = ""
        if random.randint(0, 9) == 1:
            fact_response = await features.get_fact("https://dogapi.dog/api/facts/", "facts")

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_footer(text=features.custom_footer(inter.user, "thedogapi.com"))
        embed.set_image(url=f"attachment://{file_name}")
        embeds: list[discord.Embed] = [embed]

        if fact_response:
            fact_embed = discord.Embed(
                title="Dog fact",
                description=fact_response,
                color=discord.Color.blue(),
            )
            fact_embed.set_footer(text=features.custom_footer(inter.user, "thedogapi.com"))
            embeds.append(fact_embed)

        await inter.response.send_message(file=image_file, embeds=embeds)

    @default_cooldown()
    @app_commands.command(name="fox", description=FunMess.fox_brief)
    async def fox(self, inter: discord.Interaction):
        """Get random image of a fox"""
        image_bytes, file_name = await features.get_image("https://randomfox.ca/floof/")
        image_file = discord.File(image_bytes, filename=file_name)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_footer(text=features.custom_footer(inter.user, "randomfox.ca"))
        embed.set_image(url=f"attachment://{file_name}")

        await inter.response.send_message(file=image_file, embed=embed)

    @default_cooldown()
    @app_commands.command(name="duck", description=FunMess.duck_brief)
    async def duck(self, inter: discord.Interaction):
        """Get random image of a duck"""
        image_bytes, file_name = await features.get_image(
            self.bot.morpheus_session, "https://random-d.uk/api/v2/random"
        )
        image_file = discord.File(image_bytes, filename=file_name)

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_footer(text=features.custom_footer(inter.user, "random-d.uk"))
        embed.set_image(url=f"attachment://{file_name}")

        await inter.response.send_message(file=image_file, embed=embed)

    @default_cooldown()
    @app_commands.command(name="dadjoke", description=FunMess.dadjoke_brief)
    async def dadjoke(self, inter: discord.Interaction, keyword: str = None):
        """Get random dad joke
        Arguments
        ---------
        keyword: search for a certain keyword in a joke
        """
        if keyword is not None and ("&" in keyword or "?" in keyword):
            await inter.send("I didn't find a joke like that.")
            return

        params: dict[str, str] = {"limit": "30"}
        url: str = "https://icanhazdadjoke.com"
        if keyword is not None:
            params["term"] = keyword
            url += "/search"
        headers: dict[str, str] = {"Accept": "application/json"}

        try:
            async with self.bot.morpheus_session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    raise ApiError(f"{response.status} - {response.text()}")
                fetched = await response.json()
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
            raise ApiError(error=str(error))

        if keyword is not None:
            res = fetched["results"]
            if len(res) == 0:
                await inter.send("I didn't find a joke like that.")
                return
            result = random.choice(res)
            result["joke"] = re.sub(
                f"(\\b\\w*{keyword}\\w*\\b)",
                r"**\1**",
                result["joke"],
                flags=re.IGNORECASE,
            )
        else:
            result = fetched

        embed = discord.Embed(
            title="Dadjoke",
            description=result["joke"],
            color=discord.Color.blue(),
            url="https://icanhazdadjoke.com/j/" + result["id"],
        )
        embed.set_footer(text=features.custom_footer(inter.user, "icanhazdadjoke.com"))

        await inter.response.send_message(embed=embed)

    @default_cooldown()
    @app_commands.command(name="yo_mamajoke", description=FunMess.yo_mamajoke_brief)
    async def yo_mamajoke(self, inter: discord.Interaction):
        """Get random Yo momma joke"""
        try:
            async with self.bot.morpheus_session.get("https://www.yomama-jokes.com/api/v1/jokes/random/") as response:
                if response.status != 200:
                    raise ApiError(f"{response.status} - {response.text()}")
                result = await response.json()
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
            raise ApiError(error=str(error))

        embed = discord.Embed(
            title="Yo mamajoke",
            description=result["joke"],
            color=discord.Color.blue(),
            url="https://www.yomama-jokes.com",
        )
        embed.set_footer(text=features.custom_footer(inter.user, "yomomma.info"))

        await inter.response.send_message(embed=embed)

    @default_cooldown()
    @app_commands.command(name="xkcd", description=FunMess.xkcd_brief)
    async def xkcd(self, inter: discord.Interaction, number: app_commands.Range[int, 1] = None, latest: bool = False):
        """Get random XKCD comic.
        If `latest` is specified, get the latest comic.
        If `number` is specified, get the comic with that number.
        If `number` and `latest` is specified, get comic with specified number.
        """
        await inter.response.defer()
        if not self.total_xkcd_posts:
            await self.update_xkcd_posts()

        if number:
            url = f"{self.xkcd_url}/{number}"
        elif latest:
            url = f"{self.xkcd_url}"
        else:
            number = random.randint(1, self.total_xkcd_posts)
            url = f"{self.xkcd_url}/{number}"

        xkcd_post = await features.get_xkcd(self.bot.morpheus_session, f"{url}/info.0.json")
        embed = await features.create_xkcd_embed(xkcd_post, inter.user, url)
        await inter.followup.send(embed=embed)

    @tasks.loop(time=time(12, 0, tzinfo=get_local_zone()))
    async def xkcd_daily(self):
        await self.update_xkcd_posts()
        number = random.randint(1, self.total_xkcd_posts)
        xkcd_post = await features.get_xkcd(self.bot.morpheus_session, f"{self.xkcd_url}/{number}/info.0.json")
        embed = await features.create_xkcd_embed(xkcd_post, self.bot.user, f"{self.xkcd_url}/{number}")
        for channel in self.xkcd_channels:
            await channel.send(embed=embed)
