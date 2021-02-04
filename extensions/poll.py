import discord
from discord import utils
from discord.ext import commands

from . import perms

class PollCog(commands.Cog):
    """
    Sondages
    """
    REACTIONS_YESNO = ['✅', '❌']
    REACTIONS_MULTI = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
    VOTING_CHANNEL_ID = 805511910920683530

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        message = ctx.message
        
        if ctx.command:

            if ctx.command.name == 'new_poll':
                if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
                    await message.add_reaction('\U0001F44E')
                    await ctx.send("Erreur! La commande est du type `!new_poll \"question\" nombre_max_de_vote \"opt1\" \"opt2\"...`")
            elif ctx.command.name == 'reset_poll':
                if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
                    await message.add_reaction('\U0001F44E')
                    await ctx.send("Erreur! La commande est du type `!reset_poll id`")
            elif ctx.command.name == 'destroy_poll':
                if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
                    await message.add_reaction('\U0001F44E')
                    await ctx.send("Erreur! La commande est du type `!destroy_poll id`")
            elif ctx.command.name == 'close_poll':
                if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
                    await message.add_reaction('\U0001F44E')
                    await ctx.send("Erreur! La commande est du type `!close_poll id`")

    @commands.command(name='new_poll')
    @commands.check(perms.is_support_user)
    async def new_poll(self, ctx, question: str,maxvotes: int=1, *options: str):
        """
        (Support uniquement) Faire un nouveau sondage dans le canal réservé. 
        Afin de terminer le sondage, il vous faudra faire `!closepoll <id>` ou <id> est l'identifiant du sondage 
        (indiqué en bas du sondage).
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')

        message = ctx.message
        author = ctx.author
        role_names = [r.name for  r in author.roles]
        
        voting_channel = discord.utils.get(self.bot.get_all_channels(), id=VOTING_CHANNEL_ID)
        
        if utils_cog.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction('\U0001F44E')
            await ctx.send("seuls les admins peuvent faire cette action!")
            return
        if len(options) <= 1:
            await ctx.send('Il vous faut au minimum une option')
            return
        if len(options) > 10:
            await ctx.send("Trop d'options")
            return
        
        if maxvotes < 1:
            await ctx.send('Il vous faut au minimum une option')
            return
            
        if len(options) == 2 and options[0] == 'oui' and options[1] == 'non':
            reactions = self.REACTIONS_YESNO
        else:
            reactions = self.REACTIONS_MULTI
        
        if maxvotes == 1:
            description = [f"**{maxvotes} vote max**"]
        else:
            description = [f"**{maxvotes} votes max**"]

        for x, option in enumerate(options):
            description += '\n {} {}'.format(reactions[x], option)
        
        embed = discord.Embed(title=question, description=''.join(description))
        react_message = await voting_channel.send(embed=embed)

        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        
        embed.set_footer(text=f'{maxvotes} Poll : ' + str(react_message.id))

        await react_message.edit(embed=embed)
        await ctx.send(f"Le sondage est prêt! Il se trouve sur <#{voting_channel.id}>")

    @commands.command(name='reset_poll')
    @commands.check(perms.is_support_user)
    async def reset_poll(self, ctx, id: int):
        """
        (Support uniquement) Remet tous les compteurs à un pour un sondage avec identifiant `id`. l'`id` d'un vote se trouve sous chaque vote.
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')

        message = ctx.message
        author = ctx.author
        role_names = [r.name for  r in author.roles]

        print(role_names)

        if utils_cog.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction('\U0001F44E')
            await ctx.send("seuls les admins peuvent faire cette action!")
            return
        
        called_msg = await ctx.fetch_message(id)

        if called_msg.author != bot.user:
            #chek whether bot actually posted the reacted message, otherwise ignores
            return
        
        msg_react = called_msg.reactions
        
        for r in msg_react:
            await called_msg.clear_reaction(r.emoji)
            await called_msg.add_reaction(r.emoji)

    @commands.command(name='destroy_poll')
    @commands.check(perms.is_support_user)
    async def destroy_poll(self, ctx, id: int):
        """
        (Support uniquement) détruit un sondage définitivement. Attention! Fonctionne sur tout type de message, ne vous trompez pas dans l'`id`!
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')

        message = ctx.message
        author = ctx.author
        role_names = [r.name for  r in author.roles]

        print(role_names)

        if utils_cog.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction('\U0001F44E')
            await ctx.send("seuls les admins peuvent faire cette action!")
            return

        message = await ctx.fetch_message(id)
        await message.delete()

    @commands.command(name='close_poll')
    @commands.check(perms.is_support_user)
    async def close_poll(self, ctx, id: int):
        """
        (Support uniquement) Terminer un sondage identifié par `id`. Le résultat sera inséré sous le sondage, les réactions sont remises à zéro et 
        toutes les réactions sont dorénavants accessibles.
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')

        message = ctx.message
        author = ctx.author
        role_names = [r.name for  r in author.roles]

        print(role_names)

        if utils_cog.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction('\U0001F44E')
            await ctx.send("seuls les admins peuvent faire cette action!")
            return

        called_msg = await ctx.fetch_message(id)
        
        for e in called_msg.embeds:
            #check if it's a reaction to a vote
            if ('Poll' in e.footer.text):
                description = e.description
                title = '~~'+e.title+ '~~ (terminé)'
                
        description += '\n**Résultat final:**\n'

        msg_react = called_msg.reactions
        
        for r in msg_react:
            description+= f'{r.emoji}: {r.count}\n'
            await r.clear()
        
        embed = discord.Embed(title=title, description=description)
        
        embed.set_footer(text='Sondage terminé')
        await called_msg.edit(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        channel = message.channel
        emoji = reaction.emoji

        number_of_votes = 0

        if channel.id != self.VOTING_CHANNEL_ID:
            #reacts only on vote channel are processed
            return
        
        if message.author != bot.user:
            #chek whether bot actually posted the reacted message, otherwise ignores
            return
        
        if user == bot.user:
            #ignores if it is the bot voting
            return
        
        if (emoji not in self.REACTIONS_YESNO) and (emoji not in self.REACTIONS_MULTI):
            #only vote reactions are accepted
            await reaction.remove(user)
            return
        
        for e in message.embeds:
            #check if it's a reaction to a vote
            if ('Poll' in e.footer.text):
                title = e.title
                try:
                    maxvotes = int(e.footer.text.split()[0])
                except:
                    return
                break
        else:
            return
        
        for r in message.reactions:
            users = await r.users().flatten()

            if user in users:
                number_of_votes+=1

                if number_of_votes>maxvotes:
                    await reaction.remove(user)
                    await channel.send(f'<@!{user.id}> ne peut plus voter à "{title}", c\'est son vote n°{number_of_votes}/{maxvotes}')
                    return
        
        await channel.send(f'{user.name} a voté {reaction.emoji} à "{title}", c\'est son vote n°{number_of_votes}/{maxvotes}')

def setup(bot):
    bot.add_cog(PollCog(bot))
