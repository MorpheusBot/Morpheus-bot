from __future__ import annotations

import asyncio
import io

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


async def create_nasa_embed(
    morpheus_session: aiohttp.ClientSession, author: discord.User, response: dict
) -> tuple[discord.Embed, str | None]:
    """
    Create embed for NASA API response
    """
    embed = discord.Embed(
        title=response["title"],
        description=response["explanation"],
        url=NasaMess.nasa_url,
        color=discord.Color.blurple(),
    )
    add_author_footer(embed, author)

    url = response.get("url", None)
    if response.get("media_type", None) == "video":
        return embed, url

    try:
        async with morpheus_session.get(url) as resp:
            # download image
            if resp.status != 200:
                raise ApiError(NasaMess.nasa_image_error)

            image_data = await resp.read()
            nasa_image_file = discord.File(io.BytesIO(image_data), filename="nasaImage.png")
    except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError) as error:
        raise ApiError(str(error))

    embed.set_image(url="attachment://nasaImage.png")
    return embed, nasa_image_file
