import discord
import requests
from discord.ext import tasks, commands

class WelcomeCog(commands.Cog):
    guild = None
    utils_cog = None

    channel_welcome = None

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.name.startswith('Hacking Industry Camp'):
                self.guild = guild

        self.utils_cog = self.bot.get_cog('UtilsCog')

        self.channel_welcome = discord.utils.find(lambda c: c.name == 'bienvenue', guild.channels)

        self.checkAttendeesTask.start()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        attendees = requests.get(self.utils_cog.URL_API_ATTENDEES).json()

        found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

        if found_attendee is None:
            return
        
        role = discord.utils.find(lambda r: r.name.lower() == found_attendee['role'].lower(), self.guild.roles)

        if role is None:
            return

        if role not in member.roles:
            await member.add_roles(role)
            await member.edit(nick=f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}.")
            await self.channel_welcome.send(f"Bienvenue à {member.mention} sur le Discord du Hacking Industry Camp !")

    @tasks.loop(minutes=5.0)
    async def checkAttendeesTask(self):
        await self.checkAttendees()

    async def checkAttendees(self):
        attendees = requests.get(self.utils_cog.URL_API_ATTENDEES).json()

        async for member in self.guild.fetch_members(limit=None):
            found_attendee = next((attendee for attendee in attendees if attendee["discord_unique_id"] == member.id), None)

            if found_attendee is None:
                continue
            
            role = discord.utils.find(lambda r: r.name.lower() == found_attendee['role'].lower(), self.guild.roles)

            if role is None:
                continue

            if role not in member.roles:
                await member.add_roles(role)
                await member.edit(nick=f"{found_attendee['first_name'].title()} {found_attendee['last_name'][0].upper()}.")
                await self.channel_welcome.send(f"Bienvenue à {member.mention} sur le Discord du Hacking Industry Camp !")

    @commands.command(name='checkAttendees')
    async def checkAttendeesCommand(self, ctx): 
        await self.checkAttendees()

def setup(bot):
    bot.add_cog(WelcomeCog(bot))