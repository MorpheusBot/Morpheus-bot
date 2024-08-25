from __future__ import annotations

import textwrap
from datetime import timedelta
from typing import TYPE_CHECKING, cast

import discord
import wavelink
from discord import app_commands

from database.voice import PlaylistDB
from utils.embed import PaginationView
from utils.interaction import custom_send
from utils.user import get_or_fetch_user

from .messages import VoiceMess

if TYPE_CHECKING:
    from morpheus import Morpheus

    from . import views


class Home:
    def __init__(self, channel: discord.TextChannel, voice_channel: discord.VoiceChannel):
        self.channel = channel
        self.voice_channel = voice_channel


class WavelinkPlayer(wavelink.Player):
    home: Home
    view: views.VoiceView
    message: discord.Message


class VoiceFeatures:
    @classmethod
    async def play(cls, inter: discord.Interaction, query: str, place: int = None) -> None:
        player: WavelinkPlayer = cast(WavelinkPlayer, inter.guild.voice_client)

        if not player:
            try:
                player: WavelinkPlayer = await inter.user.voice.channel.connect(cls=WavelinkPlayer, self_deaf=True)
            except AttributeError:
                await custom_send(inter, VoiceMess.join_channel, ephemeral=True)
                return
            except discord.ClientException:
                await custom_send(inter, VoiceMess.unable_to_join)
                return

        if player.autoplay == wavelink.AutoPlayMode.disabled:
            player.autoplay = wavelink.AutoPlayMode.partial

        place = place - 1 if place else None  # make it 0 based index

        # Lock the player to this channel...
        if not hasattr(player, "home"):
            player.home = Home(inter.channel, inter.guild.voice_client.channel)
        elif (player.home.channel != inter.channel) and (player.home.voice_chanel != inter.channel):
            await custom_send(inter, VoiceMess.home_channel(channel=player.home.channel.mention), ephemeral=True)
            return

        # This will handle fetching Tracks and Playlists...
        # Seed the doc strings for more information on this method...
        # If spotify is enabled via LavaSrc, this will automatically fetch Spotify tracks if you pass a URL...
        # Defaults to YouTube for non URL based queries...
        tracks: wavelink.Search = await wavelink.Playable.search(query)
        if not tracks:
            await custom_send(inter, VoiceMess.track_not_found(user=inter.user.mention), ephemeral=True)
            return

        if isinstance(tracks, wavelink.Playlist):
            # tracks is a playlist...
            if place or place == 0:
                await custom_send(inter, VoiceMess.playlist_place, ephemeral=True)
                return
            for track in tracks:
                track.extras = {"requester": inter.user.id}
            added: int = await player.queue.put_wait(tracks)
            await custom_send(inter, VoiceMess.playlist_added_queue(tracks=tracks.name, added=added, url=query))
        else:
            track: wavelink.Playable = tracks[0]
            track.extras = {"requester": inter.user.id}
            if place or place == 0:
                player.queue.put_at(place, track)
            else:
                await player.queue.put_wait(track)
            await custom_send(inter, VoiceMess.track_added_queue(track=track, url=track.uri))

        if not player.playing:
            # Play now since we aren't playing anything...
            await player.play(player.queue.get(), volume=30)

    @classmethod
    async def pause_resume(cls, player: WavelinkPlayer, user: discord.User) -> discord.Embed:
        await player.pause(not player.paused)
        if player.paused:
            description = VoiceMess.pause(user=user.mention)
        else:
            description = VoiceMess.resume(user=user.mention)
        embed = cls.create_embed(description=description)
        return embed

    @classmethod
    async def stop(cls, player: WavelinkPlayer, user: discord.User) -> discord.Embed:
        await player.disconnect()
        await player.message.edit(view=None)
        description = VoiceMess.stop(user=user.mention)
        embed = VoiceFeatures.create_embed(description=description)
        return embed

    @classmethod
    def shuffle_queue(cls, player: WavelinkPlayer, user: discord.User) -> discord.Embed:
        if not player.auto_queue.is_empty:
            player.auto_queue.shuffle()
        if not player.queue.is_empty:
            player.queue.shuffle()

        embed = cls.create_embed(description=VoiceMess.shuffle(user=user.mention))
        return embed

    @classmethod
    def get_queue(
        cls, player: WavelinkPlayer, user: discord.User
    ) -> tuple[discord.Embed, PaginationView] | tuple[None, None]:
        current_track = player.current
        if current_track:
            queue = [VoiceMess.current_track_queue(playing_emoji=VoiceMess.playing_emoji, current_track=current_track)]
        else:
            queue = []

        future_queue = []
        if player.queue:
            future_queue = [track for track in player.queue]
        if player.autoplay == wavelink.AutoPlayMode.enabled:
            future_queue = future_queue + [track for track in player.auto_queue]

        for i, track in enumerate(future_queue):
            queue.append(f"{i + 1}. [{track.title}]({track.uri}) - {track.author}")

        if not queue:
            return None, None

        embeds = []
        for i in range(0, len(future_queue), 10):
            embed = discord.Embed(title=f"Queue ({len(future_queue)} tracks)", description="\n".join(queue[i : i + 11]))
            embeds.append(embed)

        view = PaginationView(user, embeds, show_page=True)
        return embeds, view

    @classmethod
    def get_user_playlists(
        cls, playlists: list[PlaylistDB], user: discord.User, bot: Morpheus
    ) -> tuple[discord.Embed, PaginationView] | tuple[None, None]:
        embeds = []
        for i in range(0, len(playlists), 10):
            embed = discord.Embed(title="Your playlists")
            for playlist in playlists[i : i + 5]:
                if playlist.guild_id:
                    guild = bot.get_guild(int(playlist.guild_id))
                    guild_name = guild.name if guild else "Unknown"
                    name = f"{playlist.name} - {guild_name}"
                else:
                    name = playlist.name

                embed.add_field(name=name, value=f"`ID: {playlist.id}`\n{playlist.url}", inline=False)
            embeds.append(embed)

        view = PaginationView(user, embeds, show_page=True)
        return embeds, view

    @classmethod
    def create_embed(
        cls, title: str = None, description: str = None, color: discord.Color = discord.Color.dark_blue()
    ) -> discord.Embed:
        """Create an embed."""
        embed = discord.Embed(title=title, description=description, color=color)
        return embed

    @classmethod
    def now_playing_embed(
        cls, player: WavelinkPlayer, author: discord.User, recommended: bool = False
    ) -> discord.Embed:
        """Create an embed for the now playing message."""
        current_track = player.current
        description = VoiceMess.current_track(playing_emoji=VoiceMess.playing_emoji, current_track=current_track)

        embed = cls.create_embed(description=description)
        embed.set_author(name="NOW PLAYING", icon_url=author.display_avatar.url)

        if recommended:
            embed.add_field(name="Autoplay via", value=f"`{current_track.source}`", inline=True)
        else:
            embed.add_field(name="Requested by", value=author.mention, inline=True)

        embed.add_field(name="Song by", value=f"`{current_track.author}`", inline=True)

        try:
            length = timedelta(milliseconds=current_track.length)
            length = str(length).split(".")[0]  # remove milliseconds
            embed.add_field(name="Duration", value=f"`> {length}`", inline=True)
        except OverflowError:
            # probably a livestream
            embed.add_field(name="Duration", value="`Unknown`", inline=True)

        if current_track.album.name:
            embed.add_field(name="Album", value=current_track.album.name, inline=False)
        return embed

    @classmethod
    async def default_checks(
        cls, inter: discord.Interaction, player: WavelinkPlayer, check_interact: bool = True
    ) -> bool:
        """Check if the bot is connected and the user can interact."""
        if not await cls.bot_is_connected(inter, player):
            return False
        if check_interact:
            if not await cls.user_can_interact(inter, player):
                return False
        return True

    @classmethod
    async def bot_is_connected(cls, inter: discord.Interaction, player: WavelinkPlayer) -> bool:
        """Check if the bot is connected to a voice channel.

        This should not happen if so update message and return False.
        """
        if not player:
            if inter.message:
                await inter.message.edit(view=None)
            await inter.response.send_message(VoiceMess.bot_not_connected, ephemeral=True)
            return False
        return True

    @classmethod
    async def user_can_interact(cls, inter: discord.Interaction, player: WavelinkPlayer) -> bool:
        """Check if the user can interact with the bot.

        Must be in the voice channel with bot.
        """
        if inter.user not in player.channel.members:
            await inter.response.send_message(VoiceMess.not_in_channel, ephemeral=True)
            return False
        return True


class Autocomplete:
    bot: Morpheus

    @classmethod
    def truncate_string(cls, string: str, limit: int = 100) -> str:
        return textwrap.shorten(string, width=limit, placeholder="...")

    @classmethod
    async def playlist_name(cls, bot: Morpheus, playlist: PlaylistDB) -> str:
        guild = bot.get_guild(int(playlist.guild_id)) if playlist.guild_id else None
        author = await get_or_fetch_user(bot, int(playlist.author_id))
        if not guild:
            return cls.truncate_string(f"[{author.display_name}] - {playlist.name}")

        return cls.truncate_string(f"[{author.display_name} | {guild.name}] - {playlist.name}")

    @classmethod
    async def create_choices(cls, playlists: list[PlaylistDB], user_input: str) -> list[app_commands.Choice[str]]:
        playlists_found = [
            app_commands.Choice(
                name=await Autocomplete.playlist_name(cls.bot, playlist),
                value=f"{playlist.id}",
            )
            for playlist in playlists
            if user_input in playlist.name.lower()
        ][:25]
        return playlists_found

    @classmethod
    async def autocomp_play(cls, inter: discord.Interaction, user_input: str) -> list[app_commands.Choice[str]]:
        if not user_input:
            return []

        tracks: wavelink.Search = await wavelink.Playable.search(user_input, source="spsearch:")
        if not tracks:
            tracks: wavelink.Search = await wavelink.Playable.search(user_input)

        tracks_found = [
            app_commands.Choice(name=cls.truncate_string(f"{track.title} - {track.author}"), value=track.uri)
            for track in tracks[:10]
        ]

        if not tracks_found:
            return [app_commands.Choice(name=VoiceMess.no_track_found, value="")]

        return tracks_found

    @classmethod
    async def autocomp_playlists(cls, inter: discord.Interaction, user_input: str) -> list[app_commands.Choice[str]]:
        playlists = await PlaylistDB.get_available_playlists(str(inter.guild.id), str(inter.user.id))
        playlists_found = await cls.create_choices(playlists, user_input.lower())

        if not playlists_found:
            return [app_commands.Choice(name=VoiceMess.no_playlist_found, value="")]

        return playlists_found

    @classmethod
    async def autocomp_remove_playlists(
        cls, inter: discord.Interaction, user_input: str
    ) -> list[app_commands.Choice[str]]:
        playlists = await PlaylistDB.get_author_playlists(str(inter.user.id))
        playlists_found = await cls.create_choices(playlists, user_input.lower())

        if not playlists_found:
            return [app_commands.Choice(name=VoiceMess.no_playlist_found, value="")]

        return playlists_found
