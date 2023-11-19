from typing import Optional

import discord
from discord import Guild
from discord.ext import commands
from discord.ext.commands import Cog

from . import perms


class BaseCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.utils_cog: "Optional[UtilsCog]" = None
        self.guid: Optional[Guild] = None


    async def cog_load(self):
        self.utils_cog = self.bot.get_cog('UtilsCog')
        self.guild = self.utils_cog.settings.guild