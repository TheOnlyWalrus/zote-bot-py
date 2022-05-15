from discord.ext import commands


class AccessLevel:
    DENY = -999
    USER = 0
    TRUSTED = 1
    ADMIN = 2


def access_level(min_level: int):  # decorator
    async def check(ctx):
        user = await ctx.bot.db.get_user(ctx.author.id)
        if not user:  # User not in database
            await ctx.bot.db.new_user(ctx.author.id)
            return AccessLevel.USER >= min_level

        return user['access_level'] >= min_level

    return commands.check(check)


async def access_level_check(ctx, min_level: int):  # can be called anywhere
    user = await ctx.bot.db.get_user(ctx.author.id)
    if not user:  # User not in database
        await ctx.bot.db.new_user(ctx.author.id)
        return AccessLevel.USER >= min_level

    return user['access_level'] >= min_level
