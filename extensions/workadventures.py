import discord
from discord.ext import commands
from . import perms

class WorkAdventuresCog(commands.Cog):
    guild = None
    welcome_cog = None

    users_workadventures = []

    channel_help = None
    channel_bdd_workadventures = None

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(error)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.name.startswith('Hacking Industry Camp'):
                self.guild = guild

        self.welcome_cog = self.bot.get_cog('WelcomeCog')

        self.channel_help = discord.utils.find(lambda c: c.name == 'demandes-aide', guild.channels)
        self.channel_bdd_workadventures = discord.utils.find(lambda c: c.name == 'workadventures', guild.channels)

        await self.loadUsersWorkAdventures()
    
    async def loadUsersWorkAdventures(self):
        self.users_workadventures = []

        async for message in self.channel_bdd_workadventures.history(limit=None):
            content = message.content

            for line in content.split('\n'):
                data = line.split(',')

                if len(data) >= 2:
                    self.users_workadventures.append({
                        'mail': data[0].strip(),
                        'token': data[1].strip()
                    })

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel

        if channel == self.channel_bdd_workadventures:
            await self.loadUsersWorkAdventures()
    
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel_id = payload.channel_id

        if channel_id == self.channel_bdd_workadventures.id:
            await self.loadUsersWorkAdventures()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        channel_id = payload.channel_id

        if channel_id == self.channel_bdd_workadventures.id:
            await self.loadUsersWorkAdventures()

    @commands.command(name='workadventures')
    @commands.check(perms.is_support_user)
    async def workadventures(self, ctx):
        for member in self.guild.members:
            if member.bot:
                continue

            dm_channel = member.dm_channel

            if dm_channel is None:
                dm_channel = await member.create_dm()

            user_link = next((user_link for user_link in self.welcome_cog.users_link if user_link["discord_id"] == member.id), None)

            if user_link is None:
                await dm_channel.send(f"Oups ! J'ai oublié ton adresse e-mail. J’ai envoyé un message aux organisateurs pour qu’ils viennent vous aider !")
                await self.channel_help.send(f"Je ne connais pas l'adresse e-mail pour Work Adventure de {member.mention} !")
                continue

            user_workadventures = next((user_workadventures for user_workadventures in self.users_workadventures if user_workadventures['mail'] == user_link['mail']), None)
            
            if user_workadventures is None:
                await dm_channel.send(f"Ahh, je connais pas ton lien pour Work Adventure. J’ai envoyé un message aux organisateurs pour qu’ils viennent vous aider !")
                await self.channel_help.send(f"Je n'ai pas connaissance du lien pour Work Adventure de {member.mention} !")
                continue

            await dm_channel.send(f"Voici votre lien pour joindre Work Adventure du HIC : {user_workadventures['token']}")

async def setup(bot):
    await bot.add_cog(WorkAdventuresCog(bot))