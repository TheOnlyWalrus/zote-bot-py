from discord.ext import commands
from time import time_ns


class LogEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """
    TODO:
        - join, leave
        - message delete, message update
        - reaction add, reaction remove
    """

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # TODO: User voice time
        time = await self.bot.db.get_time(member.guild.id)
        time_ms = time_ns() / 1e6

        if not before.channel and after.channel:  # Joined a channel
            if guild := await self.bot.db.get_guild(member.guild.id):
                if (l := guild.get('logs')) != 0:
                    channel = member.guild.get_channel(l)
                    await channel.send(f'{time} ☎️ {member} (`{member.id}`) joined **#{after.channel.name}**')

            if await self.bot.db.get_user(member.id) is None:
                await self.bot.db.new_user(member.id)

            data = await self.bot.db.get_user(member.id)
            voice = data['voice']

            if voice.get(str(member.guild.id)) is None:
                voice[str(member.guild.id)] = {}

            voice[str(member.guild.id)]['voice_last_joined_ms'] = time_ms

            await self.bot.db.update_user(member.id, {'voice': voice})
        elif before.channel and not after.channel:  # Left a channel
            if guild := await self.bot.db.get_guild(member.guild.id):
                if (l := guild.get('logs')) != 0:
                    channel = member.guild.get_channel(l)
                    await channel.send(f'{time} ☎️ {member} (`{member.id}`) left **#{before.channel.name}**')

            if user := await self.bot.db.get_user(member.id):
                if user['voice'].get(str(member.guild.id)) is not None:
                    voice = user['voice']
                    if voice[str(member.guild.id)].get('voice_last_joined_ms', 0) != 0:
                        if voice[str(member.guild.id)].get('voice_time_spent_ms') is None:
                            voice[str(member.guild.id)]['voice_time_spent_ms'] = 0

                        voice[str(member.guild.id)]['voice_time_spent_ms'] += \
                            time_ms - voice[str(member.guild.id)]['voice_last_joined_ms']
                        voice[str(member.guild.id)]['voice_last_joined_ms'] = 0
                        await self.bot.db.update_user(member.id, {'voice': voice})
            else:
                await self.bot.db.new_user(member.id)
        elif before.channel and after.channel:  # Moved to another channel
            if guild := await self.bot.db.get_guild(member.guild.id):
                if (l := guild.get('logs')) != 0:
                    channel = member.guild.get_channel(l)
                    await channel.send(f'{time} ☎️ {member} (`{member.id}`)'
                                       f' moved from **#{before.channel.name}** to **#{after.channel.name}**')


def setup(bot):
    bot.add_cog(LogEvents(bot))
