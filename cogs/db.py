import discord
import typing

from discord.ext import commands
from utils.checks import access_level, AccessLevel


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @access_level(AccessLevel.TRUSTED)
    async def cache(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send('You must provide a valid subcommand.')

    @cache.command(name='clear')
    async def cache_clear(self, ctx):
        """Clears the cache."""
        self.bot.db.clear_cache()
        await ctx.send('Cache cleared.')

    @cache.command(name='get')
    async def cache_get(self, ctx, guild_id: typing.Optional[int] = None):
        """Gets the cache for a guild."""
        if guild_id is None:
            guild_id = ctx.guild.id

        cache = self.bot.db.guild_cache.get(guild_id)
        if cache is None:
            await ctx.send('No cache found.')
            return

        await ctx.send(f'Cache for {guild_id}: ```json\n{cache}```')

    @commands.group()
    @access_level(AccessLevel.TRUSTED)
    async def db(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send('You must provide a valid subcommand.')

    @db.command(name='guild')
    async def db_guild(self, ctx, guild_id: typing.Optional[int] = None):
        """Gets the database entry for a guild."""
        if guild_id is None:
            guild_id = ctx.guild.id

        entry = await self.bot.db.get_guild(guild_id)
        if entry is None:
            await ctx.send('No entry found.')
            return

        await ctx.send(f'Entry for {guild_id}: ```json\n{dict(entry)}```')

    @db.command(name='user')
    async def db_user(self, ctx, user: typing.Optional[discord.User] = None):
        """Gets the database entry for a user."""
        if user is None:
            user = ctx.author

        entry = await self.bot.db.get_user(user.id)
        if entry is None:
            await ctx.send('No entry found.')
            return

        await ctx.send(f'Entry for {user.id}: ```json\n{dict(entry)}```')


def setup(bot):
    bot.add_cog(Database(bot))
