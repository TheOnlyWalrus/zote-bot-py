from discord.ext import commands


class AccessLevel:
    BLACKLISTED = -1
    USER = 0
    TRUSTED = 1
    ADMIN = 2


class PermissionDenied(commands.CheckFailure):
    pass


def access_level(min_level: int):  # decorator
    async def check(ctx):
        return await access_level_check(ctx, min_level)

    return commands.check(check)


async def access_level_check(ctx, min_level: int):  # can be called anywhere
    user = await ctx.bot.db.get_user(ctx.author.id)
    if not user:  # User not in database
        await ctx.bot.db.new_user(ctx.author.id)
        return AccessLevel.USER >= min_level

    if user['access_level'] == AccessLevel.BLACKLISTED:
        raise PermissionDenied(
            'You are blacklisted from using this bot.'
            ' If you believe this is a mistake,'
            ' please contact the bot owner @ {}'.format(
                ctx.bot.get_user(ctx.bot.owner_id)
            )
        )

    return user['access_level'] >= min_level
