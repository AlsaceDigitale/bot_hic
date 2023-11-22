import os

import discord
import structlog
from discord import utils
from discord.ext import commands

log = structlog.get_logger()

DEFAULT_HELP_LINKS = "HIC|https://www.hackingindustry.camp," \
                     "Le sparkboard|https://hic2021-2.sparkboard.com," \
                     "L'agenda|canal #planning," \
                     "L'association|https://www.alsacedigitale.org"


class Settings:
    def __init__(self, bot):
        self.ADMIN_ROLE = os.getenv('BOT_ADMIN_ROLE', 'Support')
        self.SUPER_COACH_ROLE = os.getenv('BOT_SUPER_COACH_ROLE', 'SuperCoach')
        self.COACH_ROLE = os.getenv('BOT_COACH_ROLE', 'Coach')
        self.FACILITATEUR_ROLE = os.getenv('BOT_FACILITATEUR_ROLE', 'Facilitateur')
        self.PROJECT_LEAD_ROLE = os.getenv('BOT_PROJECT_LEAD_ROLE', 'Chef de Projet')
        self.ORGA_ROLE = os.getenv('BOT_ORGA_ROLE', 'Organisation')
        self.WELCOME_MODE = os.getenv('BOT_WELCOME_MODE', 'close')  # mode 'open' ou 'close'
        self.TEAM_PREFIX = os.getenv('BOT_TEAM_PREFIX', 'Equipe-')
        self.HELP_LINKS = os.getenv('BOT_HELP_LINKS', DEFAULT_HELP_LINKS)
        self.CHANNEL_HELP = os.getenv('BOT_CHANNEL_HELP', 'demandes-aide')
        self.CHANNEL_SUPPORT = os.getenv('BOT_CHANNEL_SUPPORT', 'support-technique')
        self.CHANNEL_WELCOME = os.getenv('BOT_CHANNEL_WELCOME', 'bienvenue')
        self.CHANNEL_MSG_AUTO = os.getenv('BOT_CHANNEL_MSG_AUTO', 'msg_auto')
        self.CHANNEL_VOTE = os.getenv('BOT_CHANNEL_VOTE', 'votes')
        self.PARTICIPANT_ROLE = os.getenv('BOT_PARTICIPANT_ROLE', 'Participant')
        self.TEAM_CATEGORY = os.getenv('BOT_TEAM_CATEGORY', 'Participants')
        self.JURY_ROLE = os.getenv('BOT_JURY_ROLE', 'Jury')
        self.URL_API = os.getenv('BOT_URL_API', 'https://hic-manager-dev.osc-fr1.scalingo.io')
        self.SERVER_NAME = os.getenv('SERVER_NAME', 'Hacking Industry Camp')
        self.SERVER_ID = int(os.getenv('SERVER_ID', '804784231732740106'))
        self.EVENT_NAME = os.getenv('EVENT_NAME', 'Hacking Industry Camp')
        self.EVENT_CODE = os.getenv('EVENT_CODE', 'hic-2021')
        self.EVENT_PLANNING_URL = os.getenv('EVENT_PLANNING_URL',
                                            'https://www.hackingindustry.camp/HIC2022-Planning-Previsionnel.pdf')
        self.EVENT_ICON_URL = os.getenv('EVENT_ICON_URL',
                                        'https://www.hackingindustry.camp/images/logos/Logo_HIC_White.png')

        self.bot = bot
        self.guild = None

    async def cog_load(self):
        for guild in self.bot.guilds:
            if guild.id == self.SERVER_ID:
                self.guild = guild
                break
        else:
            log.error('could not find our server', server_name=self.SERVER_NAME, server_id=self.SERVER_ID)

        log.debug('settings: ready')

    def as_string(self):
        ret = ""
        for k, v in self.__dict__.items():
            if not k.startswith('_') and k.upper() == k:
                ret += f"{k}={v}\n"

        return ret

    def get_role(self, role_code):
        setting = f"{role_code.upper()}_ROLE"
        setting_value = getattr(self, setting)

        role = discord.utils.get(self.guild.roles, name=setting_value)

        return role

    def get_channel(self, channel_code):
        setting = f"CHANNEL_{channel_code.upper()}"
        setting_value = getattr(self, setting)

        channel = discord.utils.get(self.guild.text_channels, name=setting_value)

        return channel
