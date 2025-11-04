from functools import cached_property
from typing import Optional

import discord
import requests
import structlog
from discord.errors import Forbidden
from discord.ext import tasks, commands

from extensions.base_cog import BaseCog, progress_message

log = structlog.get_logger()


class WelcomeCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    @cached_property
    def channel_welcome(self) -> discord.TextChannel:
        return self.settings.get_channel('WELCOME')

    async def cog_load(self):
        await super().cog_load()

        self.check_attendees_task.start()

    def _get_attendees_data(self):
        return requests.get(f"{self.settings.URL_API}/api/attendees/").json()

    async def welcome_member_helper(self, ctx, member: discord.Member, attendees_data=None, pedantic=True):
        if pedantic:
            log.info('welcome member', member=member.name, member_id=member.id)
        attendees = attendees_data or self._get_attendees_data()

        found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

        if found_attendee is None:
            if pedantic:
                log.warning('member not found in attendees list', member_id=member.id, member_name=member.name)
            return

        role: Optional[discord.Role] = None

        if found_attendee['role']:
            role = discord.utils.find(lambda r: r.name.lower() == found_attendee['role'].lower(),
                                      self.guild.roles)

        if role is None:
            if pedantic:
                log.warning('no role defined or found for member', member_name=member.name,
                            member_id=member.id)

        await self._rename_member(found_attendee, member, pedantic)

        if role and role not in member.roles:
            log.info('adding role to member', role=role.name, member=member.name)
            await member.add_roles(role)
            await self.channel_welcome.send(
                f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !")

    async def _rename_member(self, found_attendee, member, pedantic=True):
        new_nick = f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}"
        
        # Discord nicknames must be 32 characters or fewer
        if len(new_nick) > 32:
            # Truncate the first name if needed, keeping at least the last name initial
            max_first_name_length = 30  # 32 - 1 (space) - 1 (last name initial)
            truncated_first_name = found_attendee['first_name'].title()[:max_first_name_length]
            new_nick = f"{truncated_first_name} {found_attendee['last_name'][0].upper()}"
            
        if member.nick != new_nick:
            try:
                if pedantic:
                    log.info('renaming member', first_name=found_attendee['first_name'],
                             last_name=found_attendee['last_name'],
                             new_nick=new_nick, nick_length=len(new_nick))
                await member.edit(nick=new_nick)
            except Forbidden:
                pass

    @commands.command(name='welcome_member')
    async def welcome_member(self, ctx, member: discord.Member):
        async with progress_message(ctx, f'welcome_member {member.mention}'):
            await self.welcome_member_helper(ctx, member)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.welcome_member_helper(None, member)

    @tasks.loop(minutes=5.0)
    async def check_attendees_task(self):
        await self.check_attendees()

    async def check_attendees(self):
        log.info('check_attendees')
        attendees = self._get_attendees_data()

        async for member in self.guild.fetch_members(limit=None):
            found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id),
                                  None)
            await self.welcome_member_helper(None, member, attendees, pedantic=False)

    @commands.command(name='check_attendees')
    async def check_attendees_command(self, ctx):
        async with progress_message(ctx, 'check attendees'):
            await self.check_attendees()

    @commands.command(name='change_nicks')
    async def change_nicks(self, ctx):
        async with progress_message(ctx, 'changing nicks'):
            attendees = self._get_attendees_data()

            async for member in self.guild.fetch_members(limit=None):
                found_attendee = next(
                    (attendee for attendee in attendees if attendee["discord_unique_id"] == member.id),
                    None)

                if found_attendee is None:
                    continue

                await self._rename_member(found_attendee, member)


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
