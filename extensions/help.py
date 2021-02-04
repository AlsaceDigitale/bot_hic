import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        utils_cog = self.bot.get_cog('UtilsCog')
        for guild in self.bot.guilds:
            if guild.name.startswith('HIC 2021'):
                self.guild = guild
        self.channel_help = discord.utils.find(lambda c: c.name == utils_cog.settings.CHANNEL_HELP, guild.channels)
        self.channel_support = discord.utils.find(lambda c: c.name == utils_cog.settings.CHANNEL_SUPPORT, guild.channels)


    @commands.command(name='aide')
    async def help(self, ctx):
        """
        Commande: !help ou !aide
        Argument: /
        
        Affiche un embed avec des informations pour obtenir de l'aide
        """
        
        utils = self.bot.get_cog('UtilsCog')

        embed = discord.Embed(title="Aide")
        
        embed.description = ""
        embed.description += "==== Hacking Industry Camp - Aide ====\n"
        embed.description += "- `!help` : pour obtenir l'aide des commandes\n"
        embed.description += "- `@bénévoles` : pour appeler un bénévole\n"
        embed.description += "- `@coach` : pour être coaché\n"
        embed.description += f"- `@{utils.settings.ADMIN_ROLE}` : si quelqu'un doit passer au conseil disciplinaire\n"
        embed.description += "\n"
        embed.description += "Votez en cliquant sous les emojis. Y a un nombre max de vote!\n"

        await ctx.send(embed=embed)

    @commands.command(name='orga')
    async def orga(self, ctx):
        """
        Commande: !orga
        Argument: /
        
        Appelle à l'aide un organisateur dans le salon "demande d'aide"
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        organisateurs = discord.utils.find(lambda c: c.name == utils_cog.settings.ORGA_ROLE, self.guild.roles)        

        await self.channel_help.send(f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction('\U0001F9BE')


    @commands.command(name='coach')
    async def coach(self, ctx):
        """
        Commande: !coach
        Argument: /
        
        Appelle à l'aide un coach dans le salon "demande d'aide"
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        organisateurs = discord.utils.find(lambda c: c.name == utils_cog.settings.COACH_ROLE, self.guild.roles)        

        await self.channel_help.send(f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction('\U0001F9BE')


    @commands.command(name='support')
    async def support(self, ctx):
        """
        Commande: !support
        Argument: /
        
        Appelle à l'aide un support dans le salon "support technique"
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        organisateurs = discord.utils.find(lambda c: c.name == utils_cog.settings.ADMIN_ROLE, self.guild.roles)        

        await self.channel_support.send(f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction('\U0001F9BE')

  
def setup(bot):
    bot.add_cog(HelpCog(bot))