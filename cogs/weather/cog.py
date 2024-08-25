from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from cogs.base import Base
from custom.cooldowns import default_cooldown
from custom.custom_errors import ApiError
from utils.embed import add_author_footer

from .messages import WeatherMess

if TYPE_CHECKING:
    from morpheus import Morpheus


class Weather(Base, commands.Cog):
    def __init__(self, bot: Morpheus):
        super().__init__()
        self.bot = bot

    async def get_weather(self, place: str) -> dict:
        token = Base.config.weather_token

        url = f"http://api.openweathermap.org/data/2.5/weather?q={place}&units=metric&lang=en&appid={token}"
        try:
            async with self.bot.morpheus_session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 404:
                    return WeatherMess.place_not_found(place=place)
                elif response.status == 401:
                    return WeatherMess.token_error
                else:
                    raise ApiError(f"{response.status} - {response.text()}")
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
            raise ApiError(error=str(error))

    @default_cooldown()
    @app_commands.command(name="weather", description=WeatherMess.weather_brief)
    async def weather(self, inter: discord.Interaction, place: str = "Brno") -> None:
        await inter.response.defer()

        place = place[:100]
        if "&" in place:
            await inter.edit_original_response(content=WeatherMess.invalid_place_format(place=place))
            return

        response = await self.get_weather(place)

        if isinstance(response, str):
            await inter.edit_original_response(content=response)
            return

        description = f"Current weather in the city {response['name']}, {response['sys']['country']}"
        image = f"http://openweathermap.org/img/w/{response['weather'][0]['icon']}.png"
        weather = f"{response['weather'][0]['main']} ({response['weather'][0]['description']})"
        temp = f"{response['main']['temp']}°C"
        feels_temp = f"{response['main']['feels_like']}°C"
        humidity = f"{response['main']['humidity']}%"
        wind = f"{response['wind']['speed']}m/s"
        clouds = f"{response['clouds']['all']}%"
        visibility = f"{response['visibility'] / 1000} km" if "visibility" in response else "no data"

        embed = discord.Embed(title="Weather", description=description, color=discord.Color.blue())
        embed.set_thumbnail(url=image)
        embed.add_field(name="Weather", value=weather, inline=False)
        embed.add_field(name="Temperature", value=temp, inline=True)
        embed.add_field(name="Apparent temperature", value=feels_temp, inline=True)
        embed.add_field(name="Humidity", value=humidity, inline=True)
        embed.add_field(name="Wind", value=wind, inline=True)
        embed.add_field(name="Cloudiness", value=clouds, inline=True)
        embed.add_field(name="Visibility", value=visibility, inline=True)

        add_author_footer(embed, inter.user)

        await inter.edit_original_response(embed=embed)
