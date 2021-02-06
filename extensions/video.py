import re
import typing
import discord
import urllib.request
from discord.ext import commands

class VideoCog(commands.Cog):
    channel_videos = None

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            if guild.name.startswith('HIC 2021'):
                self.guild = guild

        self.channel_videos = discord.utils.find(lambda c: c.name == 'videos', guild.channels)
    
    @commands.command(name='video')
    async def video(self, ctx, url: str, *, message: typing.Optional[str]):
        """
        Commande: !video
        Argument: <lien> [message]
        
        Permet d'envoyé la vidéo de son équide défi
        """

        team_role = None
        for role in ctx.author.roles:
            if role.name.startswith('Equipe-Défi-'):
                team_role = role.name
                break

        if team_role is None:
            await ctx.send("Vous devez être membre d'une équipe pour utiliser cette commande !")
            return

        if team_role.lower() != ctx.channel.name:
            await ctx.send("Vous devez utiliser cette commande dans le salon de votre équipe !")
            return

        if not re.search('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url):
            await ctx.send('Vous devez spécifier un lien ! Utilisation: !video <url> [message]')
            return

        embed = discord.Embed(
            title=team_role,
            color=2013674
        )

        embed.add_field(name="Lien", value=url, inline=True)

        if message is not None:
            embed.description = message

        await self.channel_videos.send(embed=embed)
        await ctx.send("Merci pour le lien, c'est enregistré !")

        await ctx.send("J'en profite pour faire un petit test du lien...")

        try:
            with urllib.request.urlopen(url) as response:
                if response.reason == 'OK':
                    await ctx.send("OK ✅, j'arrive bien à accéder à la URL !")
                else:
                    await ctx.send(f"⚠️ ATTENTION ⚠️ : j'ai essayé d'accèder au lien et ça ne marche pas (Erreur {response.reason}), c'est peut-être pas grave mais on ne sait jamais, vérifiez ! {ctx.author.mention}")
        except urllib.request.URLError:
            await ctx.send(f"⚠️ ATTENTION ⚠️ : j'ai essayé d'accèder au lien et ça ne marche pas, c'est peut-être pas grave mais on ne sait jamais, vérifiez ! {ctx.author.mention}")

    @video.error
    async def video_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Utilisation: !video <url> [message]')

def setup(bot):
    bot.add_cog(VideoCog(bot))