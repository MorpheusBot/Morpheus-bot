from __future__ import annotations

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from morpheus import Morpheus


async def get_or_fetch_user(bot: Morpheus, user_id: int) -> discord.User | None:
    """
    Tries to get the user from the cache. If fails, it tries to
    fetch the user from the API.

    Parameters
    ----------
    user_id: :class:`int`
        The ID to search for.

    Returns
    -------
    Optional[:class:`~discord.User`]
        The user with the given ID, or ``None`` if not found.
    """
    user = bot.get_user(user_id)
    if user:
        return user

    try:
        user = await bot.fetch_user(user_id)
    except Exception:
        return None

    return user
