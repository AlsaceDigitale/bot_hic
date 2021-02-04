import discord
from discord.ext import commands

class TeamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        message = ctx.message

        if ctx.command.name == 'teamadd':
            if isinstance(error, commands.BadArgument) or (isinstance(error, commands.MissingRequiredArgument)):
                await message.add_reaction('\U0001F44E')
                await ctx.send("Erreur! La commande est du type `!teamadd nom_de_lequipe membre1 [membreX...]`")
        elif ctx.command.name == 'teamup':
            if isinstance(error, commands.BadArgument) or (isinstance(error, commands.MissingRequiredArgument)):
                await message.add_reaction('\U0001F44E')
                await ctx.send("Erreur! La commande est du type `!teamup nom_de_lequipe chef_de_projet membre1 [membreX...]`")
        

    @commands.command(name='teamadd')
    async def teamadd(self, ctx, nom_de_lequipe: discord.Role, members: commands.Greedy[discord.Member]):
        """"
        Commande: !teamadd
        Argument: nom_de_lequipe membre1 [membreX...]

        Rajouter des participants à une équipe.
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')

        message = ctx.message
        author = ctx.author
        role_names = [r.name for  r in author.roles]

        if utils_cog.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction('\U0001F44E')
            await ctx.send("seuls les admins peuvent faire cette action!")
            return
        
        for member in members:
            await member.add_roles(nom_de_lequipe)
            await ctx.message.add_reaction('\U0001F9BE')
                
    @commands.command(name='teamup')
    async def teamup(self, ctx, nom_de_lequipe: str, chef_de_projet: discord.Member, members: commands.Greedy[discord.Member]):
        """
        Commande: !teamup
        Argument: nom_de_lequipe chef_de_projet membre1 membre2 membre3

        Rajouter une equipe avec son salon.
        """
        
        utils_cog = self.bot.get_cog('UtilsCog')
        
        message = ctx.message
        author = ctx.author
        server: discord.Guild = ctx.guild
        role_names = [r.name for  r in author.roles]

        if utils_cog.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction('\U0001F44E')
            await ctx.send("seuls les admins peuvent faire cette action!")
            return
        
        serv_roles = await server.fetch_roles()
        
        teamrole: discord.Role = None

        if nom_de_lequipe not in [r.name for r in serv_roles]:
            teamrole = await server.create_role(name=nom_de_lequipe,
                                                mentionable=True,
                                                reason="admin through bot")
        else:
            await message.add_reaction('\U0001F44E')
            await ctx.send(f"L'équipe {nom_de_lequipe} existe déjà. Utilisez `!teamadd` pour rajouter des membres.")
            return
        
        # check if chefdeproj role already exists. If not, creates it.
        if 'chefdeproj' not in [r.name for r in serv_roles]:
            cdp_role = await server.create_role(name='chefdeproj',
                                            mentionable=True,
                                            reason="admin through bot")
        else:
            for r in serv_roles:
                if r.name == 'chefdeproj':
                    cdp_role = r
                    break
        
        # add the teamleader to both chefdeproj and his team's role.
        await chef_de_projet.add_roles(teamrole, cdp_role)
        
        # then each member
        for member in members:
            await member.add_roles(teamrole)
        
        await message.add_reaction('\U0001F9BE')
        
        msg = (f"Tout le monde a été rajouté dans l'équipe {teamrole.name}, et "
                f"{chef_de_projet.name} "
                f"a été rajouté aux {cdp_role.name}.\n"
                " il ne manque plus qu'un salon!")
        
        await ctx.send(msg)
        
        overwrites = {
            server.default_role: discord.PermissionOverwrite(read_messages=False),
            teamrole: discord.PermissionOverwrite(read_messages=True),
        }
        
        for r in serv_roles:
            if r.name.lower() in [utils_cog.settings.ADMIN_ROLE,'benevoles','bénévoles','coach']:
                overwrites[r]=discord.PermissionOverwrite(read_messages=True)
        
        # team_cat = await server.create_category(f'PARTICIPANTS',
        #                                             overwrites=overwrites,
        #                                             reason='Nouvelle équipe')
        
        team_cat = None
        
        for cat in server.categories:
            if cat.name=='PARTICIPANTS':
                team_cat=cat
                break
            
        if team_cat is None:
            await message.add_reaction('\U0001F44E')
            await ctx.send("Erreur! Catégorie 'PARTICIPANTS' introuvable")
            return
        
        text: discord.TextChannel = await team_cat.create_text_channel(nom_de_lequipe)
        
        perms = text.overwrites_for(teamrole)
        perms.send_messages=True
        perms.read_messages=True
        perms.attach_files=True
        perms.embed_links=True
        perms.read_message_history=True
        
        await text.set_permissions(teamrole, overwrite=perms)

        
        voice = await team_cat.create_voice_channel(nom_de_lequipe.lower())
        
        perms = voice.overwrites_for(teamrole)
        perms.connect=True
        perms.speak=True
        perms.view_channel=True
        perms.stream=True
        perms.use_voice_activation=True
        
        
        await voice.set_permissions(teamrole, overwrite=perms)
                
        msg = (f"C'est bon! <@&{teamrole.id}> vous pouvez vous rendre sur"
                f"<#{text.id}> et <#{voice.id}>.")
        
        await ctx.send(msg)
        
        await utils_cog.bot_log_message(f'Creation team <@&{teamrole.id}> OK')
        
        

def setup(bot):
    bot.add_cog(TeamCog(bot))