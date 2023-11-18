import discord
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        utils_cog = self.bot.get_cog('UtilsCog')

        for guild in self.bot.guilds:
            if guild.name.startswith('Hacking Industry Camp'):
                self.guild = guild

        self.channel_help = discord.utils.find(lambda c: c.name == utils_cog.settings.CHANNEL_HELP, guild.channels)
        self.channel_support = discord.utils.find(lambda c: c.name == utils_cog.settings.CHANNEL_SUPPORT, guild.channels)


    @commands.command(name='aide')
    async def aide(self, ctx):
        """
        Affiche un embed avec des informations pour obtenir de l'aide
        """
        
        utils = self.bot.get_cog('UtilsCog')

        embed = discord.Embed(title="==== Hacking Industry Camp - Aide ====")
        
        embed.description = "- `!help` : pour obtenir l'aide des commandes. Certains commandes fonctionnent en parlant directement avec le bot, "
        embed.description += "n'hésitez pas à lui parler directement plutôt qu'encombrer les canaux de discussion.\n"
        embed.description += "- `<@&806281615894380595>` : pour appeler **tous** les bénévole. Autrement faite !support\n"
        embed.description += "- `<@&804097679117385728>` : pour appeler **tous** les facilitateurs. Autrement faites !coach\n"
        embed.description += f"- `<@&805887766592225280>` : si quelqu'un doit passer au conseil disciplinaire. Autrement faite !orga\n"
        embed.description += "\n"
        embed.description += ("**Votes et sondages**\n"
                              f"Les sondages apparaissent dans le canal Participants > <#AREMPLACER>"
                              " Votez en cliquant sur les emojis qui se trouvent sous chaque sondage. Il y a un nombre max de votes par participant! "
                              "Une fois le sondage terminé, le résultat s'affiche et vous ne pouvez plus voter.\n"
                              "\n**LIENS**\n"
                              " - HIC: https://www.hackingindustry.camp/#/ \n"
                              " - Le sparkboard: https://hic2021-2.sparkboard.com/ \n"                             
                              " - L'agenda: <#806577615959490650> \n"
                             " - L'association: http://www.alsacedigitale.org/")
                            

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

  
async def setup(bot):
    await bot.add_cog(HelpCog(bot))
