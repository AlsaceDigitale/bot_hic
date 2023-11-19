import discord
import requests
from discord.errors import Forbidden
from discord.ext import tasks, commands

from extensions.base_cog import BaseCog


class WelcomeCog(BaseCog):
    guild = None
    utils_cog = None

    channel_welcome = None

    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        await super().cog_load()

        self.channel_welcome = discord.utils.find(lambda c: c.name == 'bienvenue', self.guild.channels)

        self.checkAttendeesTask.start()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        attendees = requests.get(f"{self.settings.URL_API}/api/attendees/").json()

        found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

        if found_attendee is None:
            return
        
        role = discord.utils.find(lambda r: r.name.lower() == found_attendee['role'].lower(), self.guild.roles)

        if role is None:
            return

        if role not in member.roles:
            await member.add_roles(role)
            await member.edit(nick=f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}.")
            await self.channel_welcome.send(f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !")

    @tasks.loop(minutes=5.0)
    async def checkAttendeesTask(self):
        await self.checkAttendees()

    async def checkAttendees(self):
        attendees = requests.get(f"{self.settings.URL_API}/api/attendees/").json()

        async for member in self.guild.fetch_members(limit=None):
            found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

            if found_attendee is None:
                continue
            
            role = discord.utils.find(lambda r: r.name.lower() == found_attendee['role'].lower(), self.guild.roles)

            if role is None:
                continue

            if role not in member.roles:
                await member.add_roles(role)
                await self.channel_welcome.send(f"Bienvenue à {member.mention} sur le Discord du {self.settings.EVENT_NAME} !")
                
                try:
                    await member.edit(nick=f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}.")
                except Forbidden:
                    pass


    @commands.command(name='checkAttendees')
    async def checkAttendeesCommand(self, ctx): 
        await self.checkAttendees()

    @commands.command(name='changeNicks')
    async def changeNicks(self, ctx):
        attendees = requests.get(self.settings.URL_API_ATTENDEES).json()

        async for member in self.guild.fetch_members(limit=None):
            found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

            if found_attendee is None:
                continue
            
            try:
                await member.edit(nick=f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}.")
            except Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))