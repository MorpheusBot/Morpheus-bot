from __future__ import annotations

import hashlib

from sqlalchemy import ARRAY, ForeignKey, LargeBinary, String, UniqueConstraint, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base, database


class GuildDB(Base):
    __tablename__ = "guild"

    id: Mapped[str] = mapped_column(primary_key=True)
    phrases: Mapped[set[GuildPhraseDB]] = relationship(back_populates="guild", cascade="all, delete", lazy="selectin")
    info_channel_id: Mapped[str] = mapped_column(nullable=True)

    @hybrid_property
    def phrases_dict(self) -> dict[str, GuildPhraseDB]:
        return {phrase.key.lower(): phrase for phrase in self.phrases}

    @classmethod
    async def get_guild(cls, guild_id: str) -> GuildDB:
        async with database.get_session() as session:
            guild = await session.execute(select(cls).where(cls.id == guild_id))
            guild = guild.scalar_one_or_none()
            return guild

    @classmethod
    async def add_guild(cls, guild_id: str) -> GuildDB:
        async with database.get_session() as session:
            guild = cls(id=guild_id)
            session.add(guild)
            await session.commit()
            await session.refresh(guild)
            return guild

    async def set_info_channel(self, channel_id: str):
        async with database.get_session() as session:
            self.info_channel_id = channel_id
            await session.commit()

    @classmethod
    async def get_phrases(cls, guild_id: str) -> dict[str, str] | None:
        async with database.get_session() as session:
            guild = await session.get(cls, guild_id)
            if not guild:
                return None
            return guild.phrases_dict

    @classmethod
    async def get_info_channel(cls, guild_id: str) -> str | None:
        async with database.get_session() as session:
            guild = await session.execute(select(cls).where(cls.id == guild_id)).scalar_one_or_none()
            if guild:
                info_channel = guild.info_channel_id if guild.info_channel_id else None
                return info_channel


class GuildPhraseDB(Base):
    __tablename__ = "guild_phrase"

    # unique key per guild
    __table_args__ = (UniqueConstraint("guild_id", "hash_key"),)

    hash_key: Mapped[str] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(nullable=False)
    guild_id: Mapped[str] = mapped_column(ForeignKey("guild.id"), nullable=False)
    guild: Mapped[GuildDB] = relationship(back_populates="phrases", lazy="selectin")
    value: Mapped[str] = mapped_column(nullable=False)
    attachment_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, default=None)
    attachment_filename: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    specific_users_id: Mapped[set[str] | None] = mapped_column(ARRAY(String), nullable=True, default=None)

    @classmethod
    def create_hash_key(cls, key) -> str:
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return hashed_key

    @classmethod
    async def get_phrase(cls, guild_id: str, key: str) -> GuildPhraseDB | None:
        async with database.get_session() as session:
            result = await session.execute(select(cls).where(cls.guild_id == guild_id, cls.key == key))
            return result.scalars().first()

    @classmethod
    async def add_phrase(
        cls,
        guild_id: str,
        key: str,
        value: str,
        attachment_data: bytes | None = None,
        attachment_filename: str | None = None,
        specific_users_id: set[str] | None = None,
    ) -> GuildPhraseDB | None:
        phrase = await cls.get_phrase(guild_id, key)
        if phrase:
            return None

        async with database.get_session() as session:
            hash_key = cls.create_hash_key(key)
            phrase = cls(
                guild_id=guild_id,
                key=key,
                hash_key=hash_key,
                value=value,
                attachment_data=attachment_data,
                attachment_filename=attachment_filename,
                specific_users_id=specific_users_id,
            )
            session.add(phrase)
            await session.commit()
            return phrase

    @classmethod
    async def remove_phrase(cls, guild_id: str, key: str) -> GuildPhraseDB | None:
        phrase = await cls.get_phrase(guild_id, key)
        if not phrase:
            return None

        async with database.get_session() as session:
            await session.delete(phrase)
            await session.commit()
            return phrase
