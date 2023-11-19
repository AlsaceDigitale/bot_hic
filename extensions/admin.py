import structlog
from discord.ext import commands

from . import perms
from .base_cog import BaseCog
from .reactions import SUCCESS, FAILURE

log = structlog.get_logger()


class AdminCog(BaseCog):
    """
    Admin
    """

    def __init__(self, bot):
        super().__init__(bot)

    @commands.check(perms.is_support_user)
    @commands.command(name='admin')
    async def admin(self, ctx):
        """
        Commande: !admin
        Argument: /
        
        Ajoute une réaction en te faisant comprendre si t'es admin ou pas :)
        """

        author = ctx.message.author
        role_names = [r.name for r in author.roles]
        log.info('checking if user is admin', user=author.name, admin_role=self.utils_cog.settings.ADMIN_ROLE)

        is_admin = self.utils_cog.settings.ADMIN_ROLE in role_names

        log.info('roles', roles=role_names, is_admin=is_admin)

        if is_admin:
            await ctx.message.add_reaction(SUCCESS)
        else:
            await ctx.message.add_reaction(FAILURE)


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
