"""
To automatically create table, import the class
"""

from database.guild import GuildDB, GuildPhraseDB
from database.voice import PlaylistDB

__all__ = ["GuildDB", "GuildPhraseDB", "PlaylistDB"]
