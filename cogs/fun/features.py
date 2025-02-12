import asyncio
import contextlib
from datetime import datetime
from io import BytesIO

import aiohttp
import discord

from custom.custom_errors import ApiError


def custom_footer(author: discord.User, url: str) -> str:
    return f"📩 {author} | {url} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"


async def get_image(morpheus_session: aiohttp.ClientSession, url: str) -> tuple[BytesIO, str] | None:
    # get random image url
    try:
        async with morpheus_session.get(url) as response:
            if response.status != 200:
                raise ApiError(response.status)
            image = await response.json()
    except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
        raise ApiError(error=str(error))

    # get image url
    if isinstance(image, list):
        url = image[0]["url"]
    else:
        url = image.get("url")
        if not url:
            url = image.get("image")

    # get image bytes
    try:
        async with morpheus_session.get(url) as response:
            if response.status != 200:
                raise ApiError(error=f"{response.status} - {response.text()}")
            file_name = url.split("/")[-1]
            return BytesIO(await response.read()), file_name
    except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as error:
        raise ApiError(error=str(error))


async def get_fact(morpheus_session: aiohttp.ClientSession, url: str, key: str) -> str:
    with contextlib.suppress(OSError):
        async with morpheus_session.get(url) as response:
            if response.status == 200:
                fact_response_ = await response.json()
                fact_response = fact_response_[key][0]
    return fact_response


async def get_xkcd(morpheus_session: aiohttp.ClientSession, url: str) -> dict:
    try:
        async with morpheus_session.get(url) as resp:
            res = await resp.json()
        return res
    except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
        return "Website unreachable"


async def create_xkcd_embed(xkcd_post: dict, user: discord.User) -> discord.Embed:
    xkcd_url = "https://xkcd.com"
    embed = discord.Embed(
        title=xkcd_post["title"],
        description=xkcd_post["alt"],
        url=xkcd_url,
    )
    embed.set_image(url=xkcd_post["img"])
    embed.set_footer(text=custom_footer(user, xkcd_url))
    return embed
