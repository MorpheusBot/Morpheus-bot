from __future__ import annotations

import io
from typing import TYPE_CHECKING

import discord
import unidecode
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import custom_cooldown, default_cooldown
from utils.general import cut_string_by_words

from .features import RestaurantsScraper
from .messages import RestaurantsMess

if TYPE_CHECKING:
    pass

restaurants = []
days = ["pondeli", "utery", "streda", "ctvrtek", "patek", "sobota", "nedele", "dnes"]


async def autocomp_restaurants(inter: discord.Interaction, user_input: str):
    return [
        app_commands.Choice(name=restaurant, value=restaurant)
        for restaurant in restaurants
        if user_input.lower() in restaurant
    ]


class Restaurants(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        global restaurants
        self.bot = bot
        self.scraper = RestaurantsScraper(self.bot.morpheus_session)
        restaurants = self.scraper.get_restaurants()

    @default_cooldown()
    @app_commands.command(name="restaurant_menu", description=RestaurantsMess.restaurant_menu_brief)
    @app_commands.autocomplete(restaurant=autocomp_restaurants)
    async def get_restaurant_menu(self, inter: discord.Interaction, restaurant: str):
        await inter.response.defer()
        await self.print_menu(inter, restaurant)

    @custom_cooldown(rate=1, per=600.0)
    @app_commands.command(name="restaurants_all", description=RestaurantsMess.restaurant_all_menus_brief)
    async def get_all_restaurants(self, inter: discord.Interaction):
        await inter.response.defer()
        restaurants = self.scraper.get_restaurants()
        for restaurant in restaurants:
            await self.print_menu(inter, restaurant)

    async def print_menu(self, inter: discord.Interaction, restaurant):
        if restaurant in restaurants:
            menu, type = await self.scraper.get_menu(restaurant)
            if type == "file":
                await inter.followup.send(
                    f"Menu z **{restaurant.upper()}**.",
                    file=discord.File(io.BytesIO(menu), filename=f"{restaurant}.jpg"),
                )
            else:
                url = self.scraper.urls[restaurant]
                await inter.followup.send(f"Menu z [**{restaurant.upper()}**]({url}).")

                # split text to lines to find days and highlight them with markdown
                menu = menu.splitlines()
                aligned_menu = []
                for line in menu:
                    if any(day in unidecode.unidecode(line.strip().lower()) for day in days):
                        line = line.lstrip(" ")
                        aligned_menu.append(f"\n# {line.title()}")
                    else:
                        aligned_menu.append(line.strip())

                # make list to string again and cut it for sending
                aligned_menu = "\n".join(aligned_menu)
                output = cut_string_by_words(aligned_menu, 1950, " ")
                for menu in output:
                    await inter.channel.send(f"```md\n{menu}```")
        else:
            await inter.followup.send("Restaurant nebyl nalezen")
