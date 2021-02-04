def is_support_user(ctx):
    utils_cog = ctx.bot.get_cog('UtilsCog')
    author = ctx.author
    role_names = [r.name for  r in author.roles]
    return utils_cog.settings.ADMIN_ROLE in role_names

def is_support_or_supercoach_user(ctx):
    utils_cog = ctx.bot.get_cog('UtilsCog')
    author = ctx.author
    role_names = [r.name for  r in author.roles]
    return (utils_cog.settings.ADMIN_ROLE in role_names) or (utils_cog.settings.SUPER_COACH_ROLE in role_names)