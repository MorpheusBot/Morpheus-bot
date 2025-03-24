from __future__ import annotations

import asyncio

import aiohttp
import discord

from custom.custom_errors import ApiError
from utils.embed import add_author_footer

from .messages import NasaMess


async def nasa_daily_image(morpheus_session: aiohttp.ClientSession, nasa_token: str) -> dict:
    url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_token}&concept_tags=True"
    try:
        async with morpheus_session.get(url) as resp:
            response = await resp.json()
            if "error" in response:
                raise ApiError(response["error"])
        return response
    except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError) as error:
        raise ApiError(str(error))


async def create_nasa_embed(author: discord.User, response: dict) -> tuple[discord.Embed, str | None]:
    """
    Create embed for NASA API response
    """
    embed = discord.Embed(
        title=response["title"],
        description=response["explanation"],
        url=NasaMess.nasa_url,
        color=discord.Color.blurple(),
    )
    url = response["hdurl"] if response.get("hdurl", None) else response.get("url", None)
    add_author_footer(embed, author)
    if response.get("media_type", None) != "video":
        embed.set_image(url=url)
        return embed, None
    return embed, url
