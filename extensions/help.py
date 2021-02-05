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
    async def aide(self, ctx):
        """
        Affiche un embed avec des informations pour obtenir de l'aide
        """
        
        utils = self.bot.get_cog('UtilsCog')

        embed = discord.Embed(title="Aide")
        
        embed.description = ""
        embed.description += "==== Hacking Industry Camp - Aide ====\n"
        embed.description += "- `!help` : pour obtenir l'aide des commandes. Certains commandes fonctionnent en parlant directement avec le bot, "
        embed.description += "n'hésitez pas à lui parler directement plutôt qu'encombrer les canaux de discussion.\n"
        embed.description += "- `@Support` : pour appeler **tous** les bénévole. Autrement faite !support\n"
        embed.description += "- `@coach` : pour appeler **tous** les facilitateurs. Autrement faites !coach\n"
        embed.description += f"- `@{utils.settings.ADMIN_ROLE}` : si quelqu'un doit passer au conseil disciplinaire. Autrement faite !orga\n"
        embed.description += "\n"
        embed.description += ("**Votes et sondages**\n"
                              f"Les sondages sont générés par le `@{utils.settings.ADMIN_ROLE}` dans le canal 'PARTICIPANTS'⇒'votes'."
                              " Votez en cliquant sur les emojis qui se trouvent sous chaque sondage. Il y a un nombre max de votes par participant! "
                              "Une fois le sondage terminé, le résultat s'affiche et vous ne pouvez plus voter.\n"
                              "\n**LIENS**"
                              "- HIC: https://www.hackingindustry.camp/#/ \n"
                              "- Le sparkboard: https://hic2021.sparkboard.com/ \n"                             
                              "- L'agenda: https://www.hackingindustry.camp/Planning-HIC-2021.pdf \n"
                             "- L'association: http://www.alsacedigitale.org/")
                            

        await ctx.send(embed=embed)

    @commands.command(name='orga')
    async def orga(self, ctx):
        """
        Appelle à l'aide un organisateur dans le salon "demande d'aide"
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        organisateurs = discord.utils.find(lambda c: c.name == utils_cog.settings.ORGA_ROLE, self.guild.roles)        

        await self.channel_help.send(f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction('\U0001F9BE')


    @commands.command(name='coach')
    async def coach(self, ctx):
        """
        Appelle à l'aide un coach dans le salon "demande d'aide"
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        organisateurs = discord.utils.find(lambda c: c.name == utils_cog.settings.COACH_ROLE, self.guild.roles)        

        await self.channel_help.send(f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction('\U0001F9BE')


    @commands.command(name='support')
    async def support(self, ctx):
        """
        Appelle à l'aide un support dans le salon "support technique"
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        organisateurs = discord.utils.find(lambda c: c.name == utils_cog.settings.ADMIN_ROLE, self.guild.roles)        

        await self.channel_support.send(f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction('\U0001F9BE')

  
def setup(bot):
    bot.add_cog(HelpCog(bot))
