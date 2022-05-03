import discord
import typing

from discord.ext import commands


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def convert_time(self, ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        return int(d), int(h), int(m), int(s), int(ms)

    @commands.group()
    async def voice(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('You must provide a valid subcommand.')

    @voice.command(name='time', description='Displays the amount of voice time a user has spent in this guild.')
    async def voice_time(self, ctx, user: typing.Optional[discord.Member] = None):
        if user is None:
            user = ctx.author

        data = await self.bot.db.get_user(user.id)
        if data is None:
            await ctx.send(f'{user} has no voice time recorded.')
            return

        if (voice := data['voice'].get(str(ctx.guild.id))) is None:
            await ctx.send(f'{user} has no voice time recorded.')
            return

        if (vt := voice.get('voice_time_spent_ms', 0)) == 0:
            await ctx.send(f'{user} has no voice time recorded.')
            return

        d, h, m, s, _ = self.convert_time(vt)

        ret = f'{user} has spent'
        if d > 0:
            ret += f' {d}d'
        if h > 0:
            ret += f' {h}h'
        if m > 0:
            ret += f' {m}m'
        if s > 0:
            ret += f' {s}s'
        await ctx.send(f'{ret} in voice channels.')

    @voice.command(name='top', description='Displays the voice time rankings in this guild.')
    async def voice_top(self, ctx):
        data = await self.bot.db.get_top_voice_times(ctx.guild.id)
        if not data:
            await ctx.send('No voice time has been recorded in this guild.')
            return

        ret = ''

        for i, (user_id, voice) in enumerate(data):
            user = self.bot.get_user(user_id)
            if user is None:
                user = 'Unknown#0000'

            d, h, m, s, _ = self.convert_time(voice['voice_time_spent_ms'])
            ret += f'{i + 1}. {user} -'
            if d > 0:
                ret += f' {d}d'
            if h > 0:
                ret += f' {h}h'
            if m > 0:
                ret += f' {m}m'
            if s > 0:
                ret += f' {s}s'
            ret += '\n'

        await ctx.send(ret)


def setup(bot):
    bot.add_cog(Information(bot))