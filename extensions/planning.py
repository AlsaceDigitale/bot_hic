import os.path
import typing
from io import BytesIO

import discord
import requests
from discord.ext import commands

from extensions import reactions
from extensions.base_cog import BaseCog

import marko

from mistletoe import Document, HtmlRenderer


class PlanningCog(BaseCog):
    """
    Planning
    """

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
        embed.add_field(name="Lien", value=self.settings.EVENT_PLANNING_URL)
        embed.set_thumbnail(url=self.settings.EVENT_ICON_URL)

        planning_filename = f'plannings/{self.settings.EVENT_CODE}.md'
        if os.path.exists(planning_filename):
            msg = open(planning_filename, 'r').read()

            with HtmlRenderer() as renderer:  # or: `with HtmlRenderer(AnotherToken1, AnotherToken2) as renderer:`
                doc = Document(msg)  # parse the lines into AST
                rendered = renderer.render(doc)  # render the AST
                embed.add_field(name="Planning", value=rendered)

            # md = marko.Markdown()
            #
            # parser = md.parser
            # renderer = md.renderer()
            # doc = parser.parse(msg)
            #
            # block_title = None
            # block_content = ""

            # for block in doc.children:
            #     if isinstance(block, marko.block.Heading):
            #         if block.level == 2:
            #             if block_title:
            #                 embed.add_field(name=block_title, value=block_content)
            #             block_title = renderer.render(block)
            #             block_content = ""
            #     else:
            #         block_content += renderer.render(block) + "\n"

        await dm_channel.send(embed=embed)
        await ctx.message.add_reaction(reactions.SUCCESS)

    # Old planning command that extracted the planning from the PDF
    async def planning_from_pdf(self, ctx, period: typing.Optional[str] = None):
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
        embed.add_field(name="Lien", value=self.settings.EVENT_PLANNING_URL)
        embed.set_thumbnail(url=self.settings.EVENT_ICON_URL)

        req = requests.get(self.settings.EVENT_PLANNING_URL, allow_redirects=True)
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
                msg_end = -1 if i + 1 >= len(idxs) else idxs[i + 1]
                msg = pdf[idx_ends[i]:msg_end]
                embed.add_field(name=field_name, value=msg)
        elif period.lower() in opt_list:
            opt = period.lower()
            period = opt_list[opt]
            field_name = pdf[idxs[period]:idx_ends[period]]
            msg_end = -1 if period + 1 >= len(idxs) else idxs[period + 1]
            msg = pdf[idx_ends[period]:msg_end]
            embed.add_field(name=field_name, value=msg)
        else:
            field_name = 'error'
            msg = "options possibles sont:\n"
            msg += "- `!planning` pour le planning entier\n"

            for k in opt_list.keys():
                msg += f"- `!planning {k}`\n"

            embed.add_field(name=field_name, value=msg)

        await dm_channel.send(embed=embed)
        await ctx.message.add_reaction(reactions.SUCCESS)


async def setup(bot):
    await bot.add_cog(PlanningCog(bot))
