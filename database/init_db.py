"""
File to initialize/drop the database.
"""

# this is to import all models so that they are recognized by Alembic
from database import *  # noqa
from database.database import Base, database


async def init_db():
    async with database.engine.begin() as conn:
        # await conn.run_sync(database.base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
