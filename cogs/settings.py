import discord
import pytz
import typing

from discord.ext import commands


class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('You must provide a valid subcommand.')

    @config.command(name='logs')
    async def config_logs(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        guild = await ctx.bot.db.get_guild(ctx.guild.id)

        if not guild:
            await ctx.bot.db.new_guild(ctx.guild.id)
            guild = await ctx.bot.db.get_guild(ctx.guild.id)

        if channel is None:
            if guild.get('logs', 0) == 0:
                await ctx.send('No logs channel set.')
            else:
                await ctx.send(f'Logging channel is set to <#{guild.get("logs")}> ({guild.get("logs")})')

            return

        if not channel.permissions_for(ctx.me).send_messages:
            await ctx.send('I do not have permission to send messages in that channel.')
            return

        await ctx.bot.db.update_guild(ctx.guild.id, {'logs': channel.id})
        await ctx.send(f'Logging channel set to {channel.mention} ({channel.id})')

    @config.command(name='timezone')
    async def config_timezone(self, ctx, *, timezone: typing.Optional[str] = None):
        guild = await ctx.bot.db.get_guild(ctx.guild.id)

        if not guild:
            await ctx.bot.db.new_guild(ctx.guild.id)
            guild = await ctx.bot.db.get_guild(ctx.guild.id)

        if timezone is None:
            await ctx.send(f'Timezone is set to {guild.get("timezone", "UTC")}')
            return

        if timezone not in pytz.all_timezones:
            await ctx.send('Invalid timezone. See <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List>'
                           ' for a list of valid timezones. Timezone must be from the `TZ database name` column.')
            return

        await ctx.bot.db.update_guild(ctx.guild.id, {'timezone': timezone})
        await ctx.send(f'Timezone set to {timezone}')

    @config.command(name='afk', description='Set the AFK voice channel.')
    async def config_afk(self, ctx, *, afk_channel: typing.Optional[discord.VoiceChannel] = None):
        guild = await ctx.bot.db.get_guild(ctx.guild.id)

        if not guild:
            await ctx.bot.db.new_guild(ctx.guild.id)
            guild = await ctx.bot.db.get_guild(ctx.guild.id)

        if afk_channel is None:
            if guild.get('afk_channel', 0) == 0:
                await ctx.send('No AFK channel set.')
            else:
                await ctx.send(f'AFK channel is set to <#{guild.get("afk_channel")}> ({guild.get("afk_channel")})')

            return

        if not afk_channel.permissions_for(ctx.me).send_messages:
            await ctx.send('I do not have permission to send messages in that channel.')
            return

        await ctx.bot.db.update_guild(ctx.guild.id, {'afk_channel': afk_channel.id})
        await ctx.send(f'AFK channel set to {afk_channel.mention} ({afk_channel.id})')


def setup(bot):
    bot.add_cog(Settings(bot))
