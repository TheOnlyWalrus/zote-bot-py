from discord.ext import commands


class AccessLevel:
    DENY = -999
    USER = 0
    TRUSTED = 1
    ADMIN = 2


def access_level(min_level: int):
    async def check(ctx):
        user = await ctx.bot.db.get_user(ctx.author.id)
        if not user:
            await ctx.bot.db.new_user(ctx.author.id)
            return AccessLevel.USER >= min_level

        return user['access_level'] >= min_level

    return commands.check(check)


async def access_level_cog(ctx, min_level: int):
    user = await ctx.bot.db.get_user(ctx.author.id)
    if not user:
        await ctx.bot.db.new_user(ctx.author.id)
        return AccessLevel.USER >= min_level

    return user['access_level'] >= min_level
