import re
import discord
from discord.ext import commands
from . import perms

class WelcomeCog(commands.Cog):
    guild = None
    utils_cog = None

    users = []
    users_link = []

    channel_welcome = None
    channel_help = None
    channel_bdd_users = None
    channel_bdd_users_link = None

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.name.startswith('HIC 2021'):
                self.guild = guild

        self.utils_cog = self.bot.get_cog('UtilsCog')

        self.channel_welcome = discord.utils.find(lambda c: c.name == 'bienvenue', guild.channels)
        self.channel_help = discord.utils.find(lambda c: c.name == 'demandes-aide', guild.channels)
        self.channel_bdd_users = discord.utils.find(lambda c: c.name == 'users', guild.channels)
        self.channel_bdd_users_link = discord.utils.find(lambda c: c.name == 'users_link', guild.channels)

        await self.loadUsers()
        await self.loadUsersLink()

    async def loadUsers(self):
        self.users = []

        async for message in self.channel_bdd_users.history(limit=None):
            content = message.content

            for line in content.split('\n'):
                data = line.split(',')

                if len(data) >= 4:
                    self.users.append({
                        'name': data[0].strip(),
                        'firstname': data[1].strip(),
                        'mail': data[2].strip(),
                        'role': data[3].strip()
                    })
    
    async def loadUsersLink(self):
        self.users_link = []

        async for message in self.channel_bdd_users_link.history(limit=None):
            content = message.content
            data = content.split(',')

            if len(data) >= 2:
                self.users_link.append({
                    'discord_id': int(data[0].strip()[3:-1]),
                    'mail': data[1].strip(),
                })

    @commands.Cog.listener()
    async def on_member_join(self, member):
        dm_channel = member.dm_channel

        if dm_channel is None:
            dm_channel = await member.create_dm()

        if self.utils_cog.settings.WELCOME_MODE == 'open':
            msg = (
                f"Bonjour {member.mention} vous débarquez ici, on dirait !\n"
                f"Je suis {self.bot.user.mention}, je suis un gentil robot et je vais vous accompagner\n"
                f"Tout d’abord pouvez-vous me donner l’adresse mail avec laquelle vous vous êtes inscrit(e) à l’évènement"
            )

            await dm_channel.send(msg)
        elif self.utils_cog.settings.WELCOME_MODE == 'close':
            msg = (
                f"Bonjour {member.mention} vous débarquez ici, on dirait !\n"
                f"Je suis {self.bot.user.mention}, je suis le gentil robot du Hacking Industry Camp\n\n"
                f"L'évenement n'a pas encore débuté ! Je reviendrai vers vous lors du lancement du HIC."
            )
        
            await dm_channel.send(msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        channel = message.channel

        if channel == self.channel_bdd_users:
            await self.loadUsers()
        elif channel == self.channel_bdd_users_link:
            await self.loadUsersLink()
        elif isinstance(channel, discord.DMChannel):
            author = message.author
            member = self.guild.get_member(author.id)

            if member is None:
                await channel.send("Vous n'êtez pas présent sur le serveur HIC 2021 !")
                return

            if len(member.roles) <= 1:
                content = message.content.strip()

                if self.utils_cog.settings.WELCOME_MODE == 'open':
                    if not re.search('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', content):
                        await channel.send("Je n'ai pas compris votre message :'(\nMerci de m'envoyer l'adresse email saisie lors de votre inscription au HIC.")
                        return

                    user = next((user for user in self.users if user["mail"] == content), None)

                    if user is None:
                        await channel.send("Désolé ! Je n’arrive pas à reconnaître votre adresse ! J’ai envoyé un message aux organisateurs pour qu’ils viennent vous aider !")
                        await self.channel_help.send(f"{member.mention} n’a pas été reconnu(e) dans la liste des participants, merci de le contacter !")
                        return
                    
                    role = discord.utils.find(lambda r: r.name == user['role'], self.guild.roles)

                    if role is None:
                        await channel.send("Désolé ! Je n’arrive pas à reconnaître le rôle que je dois t'assigner ! J’ai envoyé un message aux organisateurs pour qu’ils viennent vous aider !")
                        await self.channel_help.send(f"Le rôle {user['role']} de {member.mention} n’existe pas !")
                        return

                    await member.add_roles(role)
                    await member.edit(nick=f"{user['firstname']} {user['name'][0]}.")

                    await channel.send((
                        f"Bienvenue au HIC ! Vous êtes reconnu(e) en tant que {user['role']}, vous avez maintenant accès à l’ensemble des canaux\n"
                        f"Vous pouvez me demander de l’aide à tout moment en tapant !aide"
                    ))

                    await self.channel_welcome.send(f"Bienvenue à {member.mention} sur le Discord du Hacking Industry Camp !")
                    await self.channel_bdd_users_link.send(f"{member.mention},{user['mail']}")
                elif self.utils_cog.settings.WELCOME_MODE == 'close':
                    await channel.send((
                        f"Bonjour,\n"
                        f"Je ne suis pas en mesure de vous répondre avant le lancement du Hacking Industry Camp :'(\n"
                        f"Je reviendrai vers vous lors du lancement !"
                    ))
    
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        channel_id = payload.channel_id

        if channel_id == self.channel_bdd_users.id:
            await self.loadUsers()
        elif channel_id == self.channel_bdd_users_link.id:
            await self.loadUsersLink()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        channel_id = payload.channel_id

        if channel_id == self.channel_bdd_users.id:
            await self.loadUsers()
        elif channel_id == self.channel_bdd_users_link.id:
            await self.loadUsersLink()

    @commands.command(name='welcome_unknown')
    @commands.check(perms.is_support_user)
    async def welcome_unknow(self, ctx):
        """
        Envoie un message à toutes les personnes qui n'ont pas de grade
        """

        if self.utils_cog.settings.WELCOME_MODE == 'close':
            await ctx.send(f"Le mode Welcome est fermé !")
            return

        for member in self.guild.members:
            if len(member.roles) <= 1:
                dm_channel = member.dm_channel

                if dm_channel is None:
                    dm_channel = await member.create_dm()
     
                msg = (
                    f"Bonjour {member.mention} vous débarquez ici, on dirait !\n"
                    f"Je suis {self.bot.user.mention}, je suis un gentil robot et je vais vous accompagner\n"
                    f"Tout d’abord pouvez-vous me donner l’adresse mail avec laquelle vous vous êtes inscrit(e) à l’évènement"
                )

                await dm_channel.send(msg)


def setup(bot):
    bot.add_cog(WelcomeCog(bot))