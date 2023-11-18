import asyncio

import discord
from discord import errors
from discord.enums import ChannelType
from discord.ext import commands
import structlog 
from datetime import datetime

import os

from . import settings, perms

import traceback

log = structlog.get_logger()

class UtilsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = settings.Settings()

    async def bot_log_message(self, *args, **kwargs):
        BOT_LOG_CHANNEL_ID = os.getenv('BOT_LOG_CHANNEL_ID')

        try:
            if BOT_LOG_CHANNEL_ID:
                BOT_LOG_CHANNEL_ID = int(BOT_LOG_CHANNEL_ID)
                bot_log_channel = discord.utils.get(self.bot.get_all_channels(), id=BOT_LOG_CHANNEL_ID)
                
                if bot_log_channel:
                    await bot_log_channel.send(*args, **kwargs)
                else:
                    log.warning(f'Could not find bot log channel with id {BOT_LOG_CHANNEL_ID}')
        except Exception as e:
            log.error('Could not post message to bot log channel', exc_info=e)
            
    async def trace_exception(self, *args, exc_info=None, **kwargs):
        s=f"Exception: {args} {kwargs}\n"
        s+=traceback.format_stack()
        await self.bot_log_message(s)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(error)
        
    @commands.command(name='crash_log')
    @commands.check(perms.is_support_user)
    async def crash_log(self, ctx):
        await self.bot_log_message("Testing crash log message")
        try:
            raise "Test exception"
        except Exception as e:
            await self.trace_exception("It's only a test")
            
    @commands.command(name='show_settings')
    @commands.check(perms.is_support_user)
    async def crash_log(self, ctx):
        await self.bot_log_message("Settings")
        await self.bot_log_message("-------")
        await self.bot_log_message(self.settings.as_string())

    @commands.command(name='purge')
    @commands.check(perms.is_support_user)
    async def purge(self, ctx):
        if ctx.channel.type != ChannelType.text and ctx.channel.type != ChannelType.news:
            return

        date = datetime.now().date()
        args = ctx.message.content.split(' ')

        if len(args) >= 2:
            date = datetime.strptime(args[1], '%d/%m/%Y').date()

        async for message in ctx.history(limit=None):
            if message.created_at.date() <= date:
                await message.delete()
                await asyncio.sleep(0.1)    # rate limiting

def setup(bot):
    bot.add_cog(UtilsCog(bot))