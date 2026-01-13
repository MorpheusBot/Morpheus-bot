from __future__ import annotations

import asyncio
import os
from datetime import datetime

import aiohttp
import discord

from custom.custom_errors import ApiError
from utils.embed import add_author_footer

from .messages import NasaMess

filename = "nasaImage.png"


async def nasa_daily_image(morpheus_session: aiohttp.ClientSession) -> dict:
    url = "http://nasa-api:8000/v1/apod"
    try:
        async with morpheus_session.get(url) as resp:
            response = await resp.json()
            if "error" in response:
                raise ApiError(response["error"])
            return response
    except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError) as error:
        raise ApiError(str(error))


async def get_nasa_image(morpheus_session: aiohttp.ClientSession, response: dict) -> None:
    """
    Download NASA image from URL and save it to nasaImage.png
    """
    if os.path.exists(filename):
        os.remove(filename)

    url = response.get("url", None)
    if response.get("media_type", None) == "video" or url is None:
        return

    try:
        async with morpheus_session.get(url) as resp:
            if resp.status != 200:
                raise ApiError(NasaMess.nasa_image_error)

            with open(filename, "wb") as binary_file:
                binary_file.write(await resp.read())
    except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError) as error:
        raise ApiError(str(error))
    return


async def create_nasa_embed(author: discord.User, response: dict) -> tuple[discord.Embed, str | None]:
    """
    Create embed for NASA API response
    """

    date_str = response["date"]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%y%m%d")
    nasa_url = f"https://apod.nasa.gov/apod/ap{formatted_date}.html"

    embed = discord.Embed(
        title=response["title"],
        description=response["explanation"],
        url=nasa_url,
        color=discord.Color.blurple(),
    )
    add_author_footer(embed, author)

    url = response.get("url", None)
    if response.get("media_type", None) == "video":
        return embed, url

    embed.set_image(url=f"attachment://{filename}")
    return embed, None
