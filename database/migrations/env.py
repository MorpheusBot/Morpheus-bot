"""
This script is used to run migrations on the database.

All migration must be done inside the container for database ip resolution.
"""

import asyncio
import json
import subprocess
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from config.app_config import config as morpheus_config

# this is to import all models so that they are recognized by Alembic
from database import *  # noqa
from database.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    try:
        p = subprocess.Popen(["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = p.communicate()

        lineNumber = 1
        for line in stdout.decode("utf-8").split("\n"):
            if not line.strip():
                continue
            fields = line.split()
            if lineNumber > 1:
                containerId = fields[0]
                containerName = fields[-1]
                if "morpheus-postgres" not in containerName:
                    continue

                inspect = subprocess.run(["docker", "inspect", containerId], stdout=subprocess.PIPE)
                data = json.loads(inspect.stdout.decode("utf-8"))
                networkMode = data[0]["HostConfig"]["NetworkMode"]
                ip_address = data[0]["NetworkSettings"]["Networks"][networkMode]["IPAddress"]
                db_url = morpheus_config.db_string.replace("morpheus-postgres", ip_address)
                return db_url

            lineNumber += 1

        # Container not found, try using service name (running inside Docker)
        return morpheus_config.db_string.replace("morpheus-postgres", "postgres")

    except FileNotFoundError:
        # Docker command not found, likely running inside container
        # Use the db_string directly with service name instead of IP
        return morpheus_config.db_string.replace("morpheus-postgres", "postgres")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_async_engine(get_url())

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
