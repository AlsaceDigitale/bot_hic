import typing
from io import BytesIO

import discord
import requests
from discord.ext import commands
from pdfminer.high_level import extract_text

from extensions.base_cog import BaseCog


class PlanningCog(BaseCog):
    """
    Planning
    """
    PLANNING_URL = 'https://www.hackingindustry.camp/HIC2022-Planning-Previsionnel.pdf'

    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(name='planning', aliases=['agenda'])
    async def planning(self, ctx, period: typing.Optional[str] = None):
        """
        Commande: !planning ou !agenda
        Argument: [opt: vendredi|samedi|dimanche|semaine]
        
        Donne le planning et le lien vers le PDF.
        """
        member = ctx.author
        dm_channel = member.dm_channel

        if dm_channel is None:
            dm_channel = await member.create_dm()

        embed = discord.Embed()
        embed.add_field(name="Lien", value=self.PLANNING_URL)
        embed.set_thumbnail(url='https://www.hackingindustry.camp/images/logos/Logo_HIC_White.png')

        req = requests.get(self.PLANNING_URL, allow_redirects=True)
        bio = BytesIO(req.content)
        pdf = extract_text(bio)   

        fields = [
            'planning',
            'vendredi 25 novembre 2022',
            'samedi 26 novembre 2022',
            'dimanche 27 novembre 2022'
        ]
        
        idxs = []
        idx_ends = []
        opt_list = {'vendredi': 1, 'samedi': 2, 'dimanche': 3}
        
        for f in fields:
            try:
                idx = pdf.lower().index(f)
                idx_end = idx + len(f)
                idxs.append(idx)
                idx_ends.append(idx_end)
            except ValueError:
                pass
            
        if period is None:
            for i in range(len(idxs)):
                field_name = pdf[idxs[i]:idx_ends[i]]
                msg_end = -1 if i+1>=len(idxs) else idxs[i+1]
                msg = pdf[idx_ends[i]:msg_end]
                embed.add_field(name=field_name,value=msg)
        elif period.lower() in opt_list:
            opt = period.lower()
            period = opt_list[opt]
            field_name = pdf[idxs[period]:idx_ends[period]]
            msg_end = -1 if period+1>=len(idxs) else idxs[period+1]
            msg = pdf[idx_ends[period]:msg_end]
            embed.add_field(name=field_name,value=msg)
        else:
            field_name = 'error'
            msg = "options possibles sont:\n"
            msg += "- `!planning` pour le planning entier\n"
            
            for k in opt_list.keys():
                msg += f"- `!planning {k}`\n"
            
            embed.add_field(name=field_name,value=msg)
            
        await dm_channel.send(embed=embed)
        await ctx.message.add_reaction('\U0001F9BE')

def setup(bot):
    bot.add_cog(PlanningCog(bot))
