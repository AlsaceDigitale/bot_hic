from functools import cached_property

import discord
from discord.ext import commands

from extensions import reactions
from extensions.base_cog import BaseCog


class HelpCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        await super().cog_load()

    @cached_property
    def channel_help(self) -> discord.TextChannel:
        return self.settings.get_channel('HELP')

    @cached_property
    def channel_support(self) -> discord.TextChannel:
        return self.settings.get_channel('SUPPORT')

    @commands.command(name='aide')
    async def aide(self, ctx):
        """
        Affiche un embed avec des informations pour obtenir de l'aide
        """

        utils = self.bot.get_cog('UtilsCog')

        embed = discord.Embed(title=f"==== {utils.settings.EVENT_NAME} - Aide ====")

        # TODO: get channel ids from Discord
        embed.description = "- `!help` : pour obtenir l'aide des commandes. Certains commandes fonctionnent en parlant directement avec le bot, "
        embed.description += "n'hésitez pas à lui parler directement plutôt qu'encombrer les canaux de discussion.\n"
        # embed.description += "- `<@&806281615894380595>` : pour appeler **tous** les bénévole. Autrement faite !support\n"
        embed.description += f"- {self.settings.get_role('FACILITATEUR').mention} : pour appeler **tous** les facilitateurs. Autrement faites `!coach`\n"
        embed.description += f"- {self.settings.get_role('ORGA').mention} : si quelqu'un doit passer au conseil disciplinaire. Autrement faite `!orga`\n"
        embed.description += "\n"
        embed.description += "**Votes et sondages**\n" \
                             f"Les sondages apparaissent dans le canal {self.settings.get_channel('VOTE').mention}. " \
                             "Votez en cliquant sur les emojis qui se trouvent sous chaque sondage. Il y a un nombre max de votes par participant ! " \
                             "Une fois le sondage terminé, le résultat s'affiche et vous ne pouvez plus voter.\n"

        help_links = []

        for entry in self.settings.HELP_LINKS.split(','):
            if '|' in entry:
                k, v = entry.split('|')
                help_links.append([k, v])
            else:
                help_links.append([entry])

        if help_links:
            embed.description += "\n**LIENS**\n"

            for entry in help_links:
                embed.description += " - "
                if len(entry) == 2:
                    embed.description += f"{entry[0]}: {entry[1]}\n"
                else:
                    embed.description += f"{entry[0]}\n"

        await ctx.send(embed=embed)

    @commands.command(name='orga')
    async def orga(self, ctx):
        """
        Appelle à l'aide un organisateur dans le salon "demande d'aide"
        """

        organisateurs = discord.utils.find(lambda c: c.name == self.settings.ORGA_ROLE, self.guild.roles)

        await self.channel_help.send(
            f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction(reactions.SUCCESS)

    @commands.command(name='coach')
    async def coach(self, ctx):
        """
        Appelle à l'aide un coach dans le salon "demande d'aide"
        """
        organisateurs = discord.utils.find(lambda c: c.name == self.settings.COACH_ROLE, self.guild.roles)

        await self.channel_help.send(
            f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction(reactions.SUCCESS)

    @commands.command(name='support')
    async def support(self, ctx):
        """
        Appelle à l'aide un support dans le salon "support technique"
        """
        organisateurs = discord.utils.find(lambda c: c.name == self.settings.ADMIN_ROLE, self.guild.roles)

        await self.channel_support.send(
            f"{ctx.author.mention} appelle le groupe {organisateurs.mention} à l'aide dans le salon {ctx.message.channel.mention} !")
        await ctx.message.add_reaction(reactions.SUCCESS)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
