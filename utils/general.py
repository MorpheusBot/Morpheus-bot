from __future__ import annotations

import math
from datetime import datetime
from typing import TYPE_CHECKING

import discord
from discord import AppCommandType

if TYPE_CHECKING:
    from morpheus import Morpheus


def cut_string(string: str, part_len: int):
    return list(string[0 + i : part_len + i] for i in range(0, len(string), part_len))


def split(array, k):
    """Splits list into K parts of approximate equal length"""
    n = len(array)
    lists = [array[i * (n // k) + min(i, n % k) : (i + 1) * (n // k) + min(i + 1, n % k)] for i in range(k)]
    return lists


def split_to_parts(items, size: int) -> list:
    """Splits list into smaller lists with given size"""
    result = []

    for x in range(math.ceil(len(items) / size)):
        result.append(items[x * size : (x * size) + size])

    return result


def cut_string_by_words(string: str, part_len: int, delimiter: str) -> list:
    """returns list of strings with length of part_len, only whole words"""
    result = []
    while True:
        if len(string) < part_len:
            result.append(string)
            break
        chunk = string[:part_len]
        last_delimiter = chunk.rindex(delimiter)  # get index of last delimiter
        chunk = chunk[:last_delimiter]
        result.append(chunk)
        string = string[len(chunk) :]
    return result


def create_bar(value, total) -> str:
    prog_bar_str = ""
    prog_bar_length = 10
    percentage = 0
    if total != 0:
        percentage = value / total
        for i in range(prog_bar_length):
            if round(percentage, 1) <= 1 / prog_bar_length * i:
                prog_bar_str += "░"
            else:
                prog_bar_str += "▓"
    else:
        prog_bar_str = "░" * prog_bar_length
    prog_bar_str = prog_bar_str + f" {round(percentage * 100)}%"
    return prog_bar_str


def get_local_zone():
    return datetime.now().astimezone().tzinfo


async def get_or_fetch_channel(bot, channel_id) -> discord.TextChannel:
    channel: discord.TextChannel = bot.get_channel(channel_id)
    if channel is None:
        channel: discord.TextChannel = await bot.fetch_channel(channel_id)
    return channel


def get_commands_count(bot: Morpheus) -> dict[str, int]:
    context_commands = len(bot.commands)
    slash_commands = len(bot.tree.get_commands(type=AppCommandType.chat_input))
    message_commands = len(bot.tree.get_commands(type=AppCommandType.message))
    user_commands = len(bot.tree.get_commands(type=AppCommandType.user))
    commands_sum = context_commands + slash_commands + user_commands + message_commands

    return {
        "context": context_commands,
        "slash": slash_commands,
        "message": message_commands,
        "user": user_commands,
        "sum": commands_sum,
    }
