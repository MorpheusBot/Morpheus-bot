from __future__ import annotations

from sqlalchemy import String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base, database


class PlaylistDB(Base):
    __tablename__ = "playlist"

    __table_args__ = (UniqueConstraint("name", "author_id", "guild_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    guild_id: Mapped[str] = mapped_column(nullable=True)  # if None, it's a global playlist
    author_id: Mapped[str] = mapped_column(nullable=False, index=True)
    url: Mapped[str] = mapped_column(nullable=False)

    @classmethod
    async def get(cls, playlist_id: int) -> PlaylistDB | None:
        async with database.get_session() as session:
            result = await session.get(cls, playlist_id)
            return result

    @classmethod
    async def add_playlist(cls, guild_id: str | None, author_id: str, name: str, url: str) -> PlaylistDB | None:
        if await cls.get_playlist(guild_id, author_id, name):
            return None

        async with database.get_session() as session:
            playlist = cls(guild_id=guild_id, author_id=author_id, name=name, url=url)
            session.add(playlist)
            await session.commit()
            return playlist

    @classmethod
    async def remove_playlist(cls, inter_author_id: str, playlist_id: int) -> PlaylistDB | None:
        async with database.get_session() as session:
            playlist = await cls.get(playlist_id)
            if inter_author_id != playlist.author_id:
                return None

            await session.delete(playlist)
            await session.commit()
            return playlist

    @classmethod
    async def get_playlist(cls, guild_id: str | None, author_id: str, name: str) -> str | None:
        guild_id = None if guild_id == "None" else guild_id
        async with database.get_session() as session:
            playlist = await session.scalars(
                select(cls).where(cls.guild_id == guild_id, cls.author_id == author_id, cls.name == name)
            )
            playlist = playlist.first()
            if playlist:
                return playlist.url

        return None

    @classmethod
    async def get_author_playlists(cls, author_id: str) -> list[PlaylistDB]:
        async with database.get_session() as session:
            result = await session.scalars(select(cls).where(cls.author_id == author_id).order_by(cls.name))
            return result.all()

    @classmethod
    async def get_available_playlists(cls, guild_id: str, author_id: str) -> list[PlaylistDB]:
        my_playlists = await cls.get_author_playlists(author_id)
        guild_playlists = await cls.get_playlists_by_author_and_guild(author_id, guild_id)
        return my_playlists + guild_playlists

    @classmethod
    async def get_playlists_by_author_and_guild(cls, author_id: str, guild_id: str) -> list[PlaylistDB]:
        async with database.get_session() as session:
            result = await session.scalars(
                select(cls).where(cls.author_id != author_id, cls.guild_id == guild_id).order_by(cls.name)
            )
            return result.all()
