import contextlib
from functools import cached_property
from typing import Optional

import structlog
from discord import Guild
from discord.ext import commands

from .settings import Settings

log = structlog.get_logger()


@contextlib.asynccontextmanager
async def progress_message(ctx, task_desc):
    msg = await ctx.send(task_desc + "...")
    try:
        yield
    except Exception as e:
        await msg.edit(content=task_desc + " ❌ (exception)")
        log.exception("progress_message exception", task_desc=task_desc, exc=e)
        raise
    await msg.edit(content=task_desc + " ✅")


class BaseCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    @cached_property
    def utils_cog(self):
        return self.bot.get_cog('UtilsCog')

    @cached_property
    def settings(self) -> Settings:
        return self.utils_cog.settings

    @property
    def guild(self) -> Optional[Guild]:
        return self.settings.guild
