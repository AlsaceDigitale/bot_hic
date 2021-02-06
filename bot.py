import os
import discord
import structlog
from dotenv import load_dotenv 
from os.path import join, dirname
from discord.ext import commands

log = structlog.get_logger()

dotenv_path = join(dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    log.info('loading environment')
    load_dotenv(dotenv_path)

TOKEN = os.getenv('BOT_TOKEN')

BOT_PREFIX = os.getenv('BOT_PREFIX', '!')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=BOT_PREFIX,  case_insensitive=True, intents=intents)

@bot.event
async def on_ready():
    log.info('We have logged in as {0.user}'.format(bot))

    stream = discord.Streaming(name='Hacking Industry Camp',url='https://www.twitch.tv/alsacedigitale')
    await bot.change_presence(activity=stream)
    
    await post_version_message()

async def post_version_message():
    SCALINGO_APP=os.getenv('APP')
    SCALINGO_CONTAINER_VERSION=os.getenv('CONTAINER_VERSION')

    if SCALINGO_CONTAINER_VERSION and SCALINGO_APP:
        await bot_log_message(f"{SCALINGO_APP} a démarré en version {SCALINGO_CONTAINER_VERSION}")

async def bot_log_message(*args, **kwargs):
    BOT_LOG_CHANNEL_ID = os.getenv('BOT_LOG_CHANNEL_ID')

    try:
        if BOT_LOG_CHANNEL_ID:
            BOT_LOG_CHANNEL_ID = int(BOT_LOG_CHANNEL_ID)
            bot_log_channel = discord.utils.get(bot.get_all_channels(), id=BOT_LOG_CHANNEL_ID)
            
            if bot_log_channel:
                await bot_log_channel.send(*args, **kwargs)
            else:
                log.warning(f'Could not find bot log channel with id {BOT_LOG_CHANNEL_ID}')
    except Exception as e:
        log.error('Could not post message to bot log channel', exc_info=e)

if __name__ == "__main__":
    EXTENSIONS = [
        'extensions.help',
        'extensions.planning',
        'extensions.admin',
        'extensions.team',
        'extensions.poll',
        'extensions.utils',
        'extensions.welcome',
        'extensions.workadventures',
        'extensions.auto_message'
    ]

    for extension in EXTENSIONS:
        bot.load_extension(extension)

    bot.run(TOKEN, bot=True, reconnect=True)
