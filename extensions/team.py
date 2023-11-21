import discord
import requests
import structlog
from discord.ext import commands
from . import perms, reactions
from .base_cog import BaseCog

log = structlog.get_logger()


class TeamCog(BaseCog):
    """
    Equipes
    """

    guild = None
    utils_cog = None

    role_chef = None
    category_participants = None

    def __init__(self, bot):
        super().__init__(bot)

    async def cog_load(self):
        await super().cog_load()

        self.role_chef = discord.utils.find(lambda c: c.name == self.settings.PROJECT_LEAD_ROLE, self.guild.roles)
        self.category_participants = discord.utils.find(lambda c: c.name == self.settings.TEAM_CATEGORY,
                                                        self.guild.categories)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        message = ctx.message

        if ctx.command:
            if ctx.command.name == 'teamadd':
                if isinstance(error, commands.BadArgument) or (isinstance(error, commands.MissingRequiredArgument)):
                    await message.add_reaction(reactions.FAILURE)
                    await ctx.send("Erreur! La commande est du type `!teamadd nom_de_lequipe membre1 [membreX...]`")
            elif ctx.command.name == 'teamremove':
                if isinstance(error, commands.BadArgument) or (isinstance(error, commands.MissingRequiredArgument)):
                    await message.add_reaction(reactions.FAILURE)
                    await ctx.send("Erreur! La commande est du type `!teamremove nom_de_lequipe membre1 [membreX...]`")
            elif ctx.command.name == 'teamup':
                if isinstance(error, commands.BadArgument) or (isinstance(error, commands.MissingRequiredArgument)):
                    await message.add_reaction(reactions.FAILURE)
                    await ctx.send(
                        "Erreur! La commande est du type `!teamup nom_de_lequipe chef_de_projet membre1 [membreX...]`")
        else:
            log.error(error)

    @commands.command(name='teamadd')
    @commands.check(perms.is_support_user)
    async def teamadd(self, ctx, nom_de_lequipe: discord.Role, members: commands.Greedy[discord.Member]):
        """
        Rajouter des participants à une équipe. Déjà existante. Si vous voulez créer l'équipe, faites `!teamup`
        """
        message = ctx.message
        author = ctx.author
        role_names = [r.name for r in author.roles]

        if self.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"seuls les admins ({self.settings.ADMIN_ROLE}) peuvent faire cette action!")
            return

        if not nom_de_lequipe.name.startswith(self.settings.TEAM_PREFIX):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Le nom d'équipe doit commencer par '{self.settings.TEAM_PREFIX}' !")
            return

        for member in members:
            await member.add_roles(nom_de_lequipe)

        await ctx.message.add_reaction(reactions.SUCCESS)

    @commands.command(name='teamremove')
    @commands.check(perms.is_support_user)
    async def teamremove(self, ctx, nom_de_lequipe: discord.Role, members: commands.Greedy[discord.Member]):
        """
        Enlever des participants à une équipe.
        """
        message = ctx.message
        author = ctx.author
        role_names = [r.name for r in author.roles]

        if self.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"seuls les admins ({self.settings.ADMIN_ROLE}) peuvent faire cette action!")
            return

        if not nom_de_lequipe.name.startswith(self.settings.TEAM_PREFIX):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Le nom d'équipe doit commencer par '{self.settings.TEAM_PREFIX}' !")
            return

        for member in members:
            await member.remove_roles(nom_de_lequipe)
            await ctx.message.add_reaction(reactions.SUCCESS)

    @commands.command(name='teamlist')
    @commands.check(perms.is_support_user)
    async def teamlist(self, ctx):
        """Liste des équipes"""

        message = ctx.message
        author = ctx.author
        server: discord.Guild = ctx.guild

        role_names = [r.name for r in author.roles]

        if self.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"seuls les admins ({self.settings.ADMIN_ROLE}) peuvent faire cette action!")
            return

        roles = filter(lambda r: r.name.startswith(self.settings.TEAM_PREFIX), self.guild.roles)

        await ctx.send('\n'.join(sorted([r.name for r in roles])))

    @commands.command(name='teamdown')
    @commands.check(perms.is_support_user)
    async def teamdown(self, ctx, nom_de_lequipe: str):
        """Supprimer une équipe"""

        role = nom_de_lequipe

        if not nom_de_lequipe.startswith("<@"):
            role = discord.utils.find(lambda r: r.name == nom_de_lequipe, self.guild.roles)
        else:
            role = discord.utils.get(self.guild.roles, id=int(nom_de_lequipe[3:-1]))
            nom_de_lequipe = role.name

        message = ctx.message
        author = ctx.author
        server: discord.Guild = ctx.guild

        role_names = [r.name for r in author.roles]

        if self.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"seuls les admins ({self.settings.ADMIN_ROLE}) peuvent faire cette action!")
            return

        if not role.name.startswith(self.settings.TEAM_PREFIX):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Le nom d'équipe doit commencer par '{self.settings.TEAM_PREFIX}' !")
            return

        log.info('destroying team', role=role)

        if role is None:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send('Rôle non trouvé')
        else:
            members = []

            for member in server.members:
                if role in member.roles:
                    members.append(member)

            log.info('members', member=[m.name for m in members])

            log.info('removing roles of members')

            for m in members:
                await m.remove_roles(role)

            log.info('removing role')

            await role.delete()

            await ctx.send('Rôle supprimé')

        log.info('removing channels')

        channels = []

        voice_channel = discord.utils.find(lambda c: c.name == nom_de_lequipe.lower(), server.voice_channels)

        if voice_channel:
            log.info('found voice channel', channel=voice_channel)
            channels.append(voice_channel)

        text_channel = discord.utils.find(lambda c: c.name == nom_de_lequipe.lower(), server.text_channels)

        if text_channel:
            log.info('found text channel', channel=text_channel)
            channels.append(text_channel)

        for c in channels:
            log.info(f'deleting channel {c}')
            await c.delete(reason='deleted team')
            await ctx.send(f'Canal {c.name} supprimé')
            await message.add_reaction(reactions.SUCCESS)

        await ctx.send(f'Equipe {nom_de_lequipe} supprimée')

    @commands.command(name='teamup')
    @commands.check(perms.is_support_user)
    async def teamup(self, ctx, nom_de_lequipe: str, chef_de_projet: discord.Member,
                     members: commands.Greedy[discord.Member]):
        f"""
        Rajouter des participants à une équipe. Le chef de projet est rajouté au rôle `chefdeproj`. L'équipe aura accès à un canal textuel et un canal oral. A noter:
        tous les noms d'équipes doivent commencer par '{self.bot.get_cog('UtilsCog').settings.TEAM_PREFIX}'!
        """
        utils_cog = self.bot.get_cog('UtilsCog')

        message = ctx.message
        author = ctx.author
        server: discord.Guild = ctx.guild
        role_names = [r.name for r in author.roles]

        if self.settings.ADMIN_ROLE not in role_names:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"seuls les admins ({self.settings.ADMIN_ROLE}) peuvent faire cette action!")
            return

        if not nom_de_lequipe.startswith(self.settings.TEAM_PREFIX):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Le nom d'équipe doit commencer par '{self.settings.TEAM_PREFIX}' !")
            return

        serv_roles = await server.fetch_roles()

        teamrole: discord.Role = None
        cdp_role: discord.Role = None

        if nom_de_lequipe not in [r.name for r in serv_roles]:
            teamrole = await server.create_role(name=nom_de_lequipe,
                                                mentionable=True,
                                                reason="admin through bot")
        else:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"L'{nom_de_lequipe} existe déjà. Utilisez `!teamadd` pour rajouter des membres.")
            return

        # check if chefdeproj role already exists. If not, creates it.
        if self.settings.PROJECT_LEAD_ROLE not in [r.name for r in serv_roles]:
            cdp_role = await server.create_role(name=self.settings.PROJECT_LEAD_ROLE,
                                                mentionable=True,
                                                reason="admin through bot")
        else:
            for r in serv_roles:
                if r.name == self.settings.PROJECT_LEAD_ROLE:
                    cdp_role = r
                    break

        # add the teamleader to both chefdeproj and his team's role.
        await chef_de_projet.add_roles(teamrole, cdp_role)

        # then each member
        for member in members:
            await member.add_roles(teamrole)

        await message.add_reaction(reactions.SUCCESS)

        msg = (f"Tout le monde a été rajouté dans l'{teamrole.name}, et "
               f"{chef_de_projet.name} "
               f"a été rajouté aux {cdp_role.name}.\n"
               f"il ne manque plus qu'un salon!")

        await ctx.send(msg)

        overwrites = {
            server.default_role: discord.PermissionOverwrite(read_messages=False),
            teamrole: discord.PermissionOverwrite(read_messages=True),
        }

        for r in serv_roles:
            if r.name.lower() in [self.settings.ADMIN_ROLE, 'benevoles', 'bénévoles', 'coach']:
                overwrites[r] = discord.PermissionOverwrite(read_messages=True)

        # team_cat = await server.create_category(f'PARTICIPANTS',
        #                                             overwrites=overwrites,
        #                                             reason='Nouvelle équipe')

        team_cat = None

        for cat in server.categories:
            if cat.name == self.settings.TEAM_CATEGORY:
                team_cat = cat
                break

        if team_cat is None:
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Erreur! Catégorie '{self.settings.TEAM_CATEGORY}' introuvable")
            return

        text: discord.TextChannel = await team_cat.create_text_channel(nom_de_lequipe)

        perms = text.overwrites_for(teamrole)
        perms.send_messages = True
        perms.read_messages = True
        perms.attach_files = True
        perms.embed_links = True
        perms.read_message_history = True

        await text.set_permissions(teamrole, overwrite=perms)

        voice = await team_cat.create_voice_channel(nom_de_lequipe.lower())

        perms = voice.overwrites_for(teamrole)
        perms.connect = True
        perms.speak = True
        perms.view_channel = True
        perms.stream = True
        perms.use_voice_activation = True

        await voice.set_permissions(teamrole, overwrite=perms)

        msg = (f"C'est bon! <@&{teamrole.id}> vous pouvez vous rendre sur"
               f"<#{text.id}> et <#{voice.id}>.")

        await ctx.send(msg)

        await utils_cog.bot_log_message(f'Creation team <@&{teamrole.id}> OK')

    ####SUPERCOACH

    @commands.command(name='teamcoachadd')
    @commands.check(perms.is_support_or_supercoach_user)
    async def teamcoachadd(self, ctx, nom_de_lequipe: discord.Role, member: discord.Member):
        """
        Rajouter un coach à une équipe.
        """
        message = ctx.message
        author = ctx.author
        role_names = [r.name for r in author.roles]
        member_role_names = [r.name for r in member.roles]

        if (self.settings.ADMIN_ROLE not in role_names) and (
                self.settings.SUPER_COACH_ROLE not in role_names):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(
                f"Seuls les admins ({self.settings.ADMIN_ROLE}) et les Super Coach ({self.settings.SUPER_COACH_ROLE}) peuvent faire cette action!")
            return

        if not nom_de_lequipe.name.startswith(self.settings.TEAM_PREFIX):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Le nom d'équipe doit commencer par '{self.settings.TEAM_PREFIX}' !")
            return

        if (self.settings.COACH_ROLE not in member_role_names) and (
                self.settings.SUPER_COACH_ROLE not in member_role_names) and (
                self.settings.FACILITATEUR_ROLE not in member_role_names):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(
                f"Seuls les coachs, les Super Coach et les facilitateurs peuvent se faire ajouter à des équipe !")
            return

        await member.add_roles(nom_de_lequipe)
        await ctx.message.add_reaction(reactions.SUCCESS)

    @commands.command(name='teamcoachremove')
    @commands.check(perms.is_support_or_supercoach_user)
    async def teamcoachremove(self, ctx, nom_de_lequipe: discord.Role, member: discord.Member):
        """
        Enlever un coach d'une équipe.
        """
        message = ctx.message
        author = ctx.author
        role_names = [r.name for r in author.roles]
        member_role_names = [r.name for r in member.roles]

        if (self.settings.ADMIN_ROLE not in role_names) and (
                self.settings.SUPER_COACH_ROLE not in role_names):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(
                f"Seuls les Admins ({self.settings.ADMIN_ROLE}) et les Super Coach ({self.settings.SUPER_COACH_ROLE}) peuvent faire cette action!")
            return

        if not nom_de_lequipe.name.startswith(self.settings.TEAM_PREFIX):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(f"Le nom d'équipe doit commencer par '{self.settings.TEAM_PREFIX}' !")
            return

        if (self.settings.COACH_ROLE not in member_role_names) and (
                self.settings.SUPER_COACH_ROLE not in member_role_names) and (
                self.settings.FACILITATEUR_ROLE not in member_role_names):
            await message.add_reaction(reactions.FAILURE)
            await ctx.send(
                f"Seuls les coachs, les Super Coach et les facilitateurs peuvent se faire retirer à des équipe !")
            return

        await member.remove_roles(nom_de_lequipe)
        await ctx.message.add_reaction(reactions.SUCCESS)

    @commands.command(name='teamapi')
    async def teamapi(self, ctx):
        project_teams = requests.get(f"{self.settings.URL_API}/api/project-teams/").json()

        for project_team in project_teams:
            if project_team['event'] != self.settings.EVENT_CODE:
                continue

            name_team = f"{self.settings.TEAM_PREFIX}{project_team['number']}"

            role_team = discord.utils.find(lambda r: r.name == name_team, self.guild.roles)

            if role_team is None:
                role_team = await ctx.guild.create_role(name=name_team, mentionable=True)

            text_channel_team = discord.utils.find(lambda r: r.name.lower() == name_team.lower(),
                                                   self.category_participants.text_channels)

            if text_channel_team is None:
                text_channel_team = await self.category_participants.create_text_channel(name_team)

                perms = text_channel_team.overwrites_for(role_team)
                perms.view_channel = True
                perms.send_messages = True

                await text_channel_team.set_permissions(role_team, overwrite=perms)

            voice_channel_team = discord.utils.find(lambda r: r.name.lower() == name_team.lower(),
                                                    self.category_participants.voice_channels)

            if voice_channel_team is None:
                voice_channel_team = await self.category_participants.create_voice_channel(name_team.lower())

                perms = voice_channel_team.overwrites_for(role_team)
                perms.view_channel = True

                await voice_channel_team.set_permissions(role_team, overwrite=perms)

            leader_team = discord.utils.find(lambda r: r.id == project_team['leader']['discord_unique_id'],
                                             self.guild.members)

            if leader_team is not None:
                leader_team_roles = [r.name for r in leader_team.roles]

                if name_team not in leader_team_roles:
                    await leader_team.add_roles(role_team)
                    await leader_team.add_roles(self.role_chef)

            for member_team_data in project_team['members']:
                member_team = discord.utils.find(lambda r: r.id == member_team_data['discord_unique_id'],
                                                 self.guild.members)

                if member_team is not None:
                    member_team_roles = [r.name for r in member_team.roles]

                    if name_team not in member_team_roles:
                        await member_team.add_roles(role_team)


async def setup(bot):
    await bot.add_cog(TeamCog(bot))
