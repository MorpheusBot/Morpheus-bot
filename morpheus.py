import logging
import os
import platform

import aiohttp
import discord
import git
import wavelink
from discord.ext import commands

from config.app_config import config
from config.messages import GlobalMessages
from database.init_db import init_db
from utils.embed import info_embed
from utils.general import get_commands_count


class Morpheus(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="?", intents=discord.Intents.all())
        self.bot_handler = logging.FileHandler(filename="logs/morpheus.log", encoding="utf-8", mode="w")
        self.bot_formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")

        discord.utils.setup_logging(handler=self.bot_handler, formatter=self.bot_formatter)

    async def setup_hook(self) -> None:
        # initialize database
        await init_db()
        logging.info("Database initialized")

        # connect to lavalink
        port = os.environ.get("SERVER_PORT", 2333)
        password = os.environ.get("LAVALINK_SERVER_PASSWORD", "youshallnotpass")
        nodes = [wavelink.Node(uri=f"ws://lavalink:{port}", password=password)]
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=None)

        # get bot data
        await self.application_info()

        # create aiohttp session
        headers = {"User-Agent": f"https://github.com/solumath/Morpheus?bot_owner={self.owner_id}"}
        self.morpheus_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=headers)

        # load cogs
        await self.init_cogs()

    async def on_ready(self) -> None:
        synced = await self.tree.sync()
        commands = get_commands_count(self)

        ready_string = f"Logged in as {self.user.mention} | {self.user.id}\n"
        ready_string += f"Python {platform.python_version()}\n"
        ready_string += f"Discordpy {discord.__version__}\n"
        ready_string += f"Synced {len(synced)} commands\n"
        ready_string += f"Latency: {round(self.latency * 1000)} ms\n"
        ready_string += f"Connected to {len(self.guilds)} guilds\n"
        ready_string += GlobalMessages.commands_count(
            sum=commands.get("sum", "Missing"),
            context=commands.get("context", "Missing"),
            slash=commands.get("slash", "Missing"),
            message=commands.get("message", "Missing"),
            user=commands.get("user", "Missing"),
        )

        embed: discord.Embed = info_embed(self)
        embed.add_field(name="Synced commands", value=f"{len(synced)}")

        # set status for bot
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        await self.change_presence(activity=discord.Game(f"On commit {sha[:7]}"))
        bot_room: discord.TextChannel = self.get_channel(config.bot_dev_channel)
        if bot_room is not None:
            await bot_room.send(embed=embed)

        logging.info(ready_string)

    async def init_cogs(self) -> None:
        """Loads all cogs from the cogs folder"""
        for cog in config.extensions:
            await self.load_extension(f"cogs.{cog}")
            logging.info(f"Loaded {cog}")


morpheus = Morpheus()

morpheus.run(config.key)
