import discord
import typing

from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_log = self.bot.get_cog('LogEvents').send_log  # Get the send_log function from LogEvents cog

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: typing.Optional[str] = 'No reason provided.'):
        if not ctx.guild:  # no clue how this could happen, but just incase
            return

        # Check if bot has permission to ban
        if not ctx.guild.me.guild_permissions.kick_members:
            await ctx.send('I do not have permission to kick members.')
            return

        # Check role level
        if not (ctx.author.top_role.position > member.top_role.position) or ctx.author == member:
            await ctx.send('You cannot kick this user.')
            return

        # Check bot role level
        if not (ctx.guild.me.top_role.position > member.top_role.position) or ctx.guild.me == member:
            await ctx.send('I cannot kick this user.')
            return

        try:
            await member.kick(reason=reason)
            await self.send_log(
                ctx.guild, f'🚨 {member} (`{member.id}`) was kicked by {ctx.author} (`{ctx.author.id}`) for {reason}'
            )
            await ctx.send(f'{member} was kicked.')
        except discord.Forbidden:
            await ctx.send('Something went wrong.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: typing.Union[discord.Member, discord.User], *,
                  reason: typing.Optional[str] = 'No reason provided.'):
        if not ctx.guild:  # no clue how this could happen, but just incase
            return

        # Check if bot has permission to kick
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send('I do not have permission to ban members.')
            return

        # Check role level
        if not isinstance(member, discord.User) and \
                (not (ctx.author.top_role.position > member.top_role.position) or ctx.author == member):
            await ctx.send('You cannot ban this user.')
            return

        # Check bot role level
        if not isinstance(member, discord.User) and \
                (not (ctx.guild.me.top_role.position > member.top_role.position) or ctx.guild.me == member):
            await ctx.send('I cannot ban this user.')
            return

        try:
            await ctx.guild.ban(member, reason=reason)  # ctx.guild.ban incase the user is not in the guild
            await self.send_log(
                ctx.guild, f'🚨 {member} (`{member.id}`) was banned by {ctx.author} (`{ctx.author.id}`) for {reason}'
            )
            await ctx.send(f'{member} was banned.')
        except discord.Forbidden:
            await ctx.send('Something went wrong.')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: typing.Union[discord.User], *,
                    reason: typing.Optional[str] = 'No reason provided.'):
        if not ctx.guild:  # no clue how this could happen, but just incase
            return

        # Check if bot has permission to ban
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.send('I do not have permission to (un)ban members.')
            return

        try:
            await ctx.guild.unban(user, reason=reason)
            await self.send_log(
                ctx.guild, f'🚨 {user} (`{user.id}`) was banned by {ctx.author} (`{ctx.author.id}`) for {reason}'
            )
            await ctx.send(f'{user} was unbanned.')
        except discord.Forbidden:
            await ctx.send('Something went wrong.')


def setup(bot):
    bot.add_cog(Moderation(bot))
