from discord.ext import commands
from time import time_ns


class LogEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, guild, message):
        if guild is None:  # User dm
            return

        time = await self.bot.db.get_time(guild.id)  # Get the current time for guild timezone

        if _guild := await self.bot.db.get_guild(guild.id):  # Get the guild data
            if (l := _guild.get('logs', 0)) != 0:
                channel = guild.get_channel(l)
                await channel.send(f'{time} {message}')

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if user.bot:
            return

        if not guild:  # should never happen but just incase
            return

        await self.send_log(guild, f'🚨 {user} (`{user.id}`) was banned')

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if user.bot:
            return

        if not guild:  # should never happen but just incase
            return

        await self.send_log(guild, f'🚨 {user} (`{user.id}`) was unbanned')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return

        if payload.member is None is None or payload.member.bot:
            return

        guild_data = await self.bot.db.get_guild(payload.guild_id)
        if r := guild_data.get('rolemenu', {}):
            try:
                guild = self.bot.get_guild(payload.guild_id)

                channel = guild.get_channel(payload.channel_id)
                if channel is None:
                    return

                message = await channel.fetch_message(payload.message_id)
                if message is None:
                    return

                if payload.emoji.id is None:
                    role_id = r[str(channel.id)][str(message.id)][str(payload.emoji.name)]
                else:
                    role_id = r[str(channel.id)][str(message.id)][str(payload.emoji.id)]

                guild_roles = await guild.fetch_roles()
                roles = list(filter(lambda _r: int(_r.id) == int(role_id), guild_roles))

                if len(roles) < 1:
                    return

                role = roles[0]

                if role.id in [r.id for r in payload.member.roles]:
                    return

                try:
                    await payload.member.add_roles(role)
                finally:
                    return
            except KeyError as e:  # No rolemenu data for this event
                return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        member = await guild.fetch_member(payload.user_id)

        if member is None or member.bot:
            return

        guild_data = await self.bot.db.get_guild(payload.guild_id)
        if r := guild_data.get('rolemenu', {}):
            try:
                channel = guild.get_channel(payload.channel_id)
                if channel is None:
                    return

                message = await channel.fetch_message(payload.message_id)
                if message is None:
                    return

                if payload.emoji.id is None:
                    role_id = r[str(channel.id)][str(message.id)][str(payload.emoji.name)]
                else:
                    role_id = r[str(channel.id)][str(message.id)][str(payload.emoji.id)]

                guild_roles = await guild.fetch_roles()
                roles = list(filter(lambda _r: int(_r.id) == int(role_id), guild_roles))

                if len(roles) < 1:
                    return

                role = roles[0]

                if role.id not in [r.id for r in member.roles]:
                    return

                try:
                    await member.remove_roles(role)
                finally:
                    return
            except KeyError as e:  # No rolemenu data for this event
                return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(member.guild, f'📥 {member} (`{member.id}`) joined the server.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        bans = await member.guild.bans()
        # check if user left because of being banned
        filtered = list(filter(lambda entry: entry.user.id == member.id, bans))

        if filtered:  # list is not empty, this user has been banned
            return

        await self.send_log(member.guild, f'📤 {member} (`{member.id}`) left the server.')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.guild is None:
            return

        if before.bot:
            return

        if before.nick != after.nick:
            await self.send_log(before.guild, f'🔄 {before} (`{before.id}`) nickname changed:\n'
                                              f'`{before.nick}` → `{after.nick}`')

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        attch = [
            m.url for m in message.attachments
        ]
        s = f'🗑️ {message.author} (`{message.author.id}`) message deleted in **#{message.channel.name}**:\n' \
            f'{message.content}\n' \
            'Attachments:\n' + ('\n'.join(attch) if attch else 'None')

        await self.send_log(message.guild, s)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.guild is None:
            return

        if before.pinned != after.pinned:
            return

        if before.author.bot:
            return

        if before.content != after.content:
            await self.send_log(before.guild, f'✏️ {before.author} (`{before.author.id}`) message edited in'
                                f' **#{before.channel.name}**:\n**B:** {before.content}\n**A:** {after.content}')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        time_ms = time_ns() / 1e6

        if member.bot:
            return

        user = await self.bot.db.get_user(member.id)
        if user is None:
            await self.bot.db.new_user(member.id)
            user = await self.bot.db.get_user(member.id)

        guild = await self.bot.db.get_guild(member.guild.id)

        if not before.channel and after.channel:  # Joined a channel
            await self.send_log(member.guild, f'☎️  {member} (`{member.id}`) joined **#{after.channel.name}**')
            if guild is not None and guild.get('afk_channel', 0) == after.channel.id:
                return

            voice = user['voice']

            if voice.get(str(member.guild.id)) is None:
                voice[str(member.guild.id)] = {}

            voice[str(member.guild.id)]['voice_last_joined_ms'] = time_ms

            await self.bot.db.update_user(member.id, {'voice': voice})
        elif before.channel and not after.channel:  # Left a channel
            await self.send_log(member.guild, f'☎️ {member} (`{member.id}`) left **#{before.channel.name}**')

            if guild is not None and guild.get('afk_channel', 0) == before.channel.id:
                return

            if user['voice'].get(str(member.guild.id)) is not None:
                voice = user['voice']
                if voice[str(member.guild.id)].get('voice_last_joined_ms', 0) != 0:
                    if voice[str(member.guild.id)].get('voice_time_spent_ms') is None:
                        voice[str(member.guild.id)]['voice_time_spent_ms'] = 0

                    voice[str(member.guild.id)]['voice_time_spent_ms'] += \
                        time_ms - voice[str(member.guild.id)]['voice_last_joined_ms']
                    voice[str(member.guild.id)]['voice_last_joined_ms'] = 0
                    await self.bot.db.update_user(member.id, {'voice': voice})
        elif before.channel and after.channel:  # Moved to another channel
            # TODO: afk_channel column in db and stop recording voice time if moving to afk, or if moving out of afk start recording again
            if before.channel == after.channel:
                return

            await self.send_log(member.guild, f'☎️ {member} (`{member.id}`)'
                                f' moved from **#{before.channel.name}** to **#{after.channel.name}**')

            if guild is not None and guild['afk_channel'] == before.channel.id:  # Moving out of afk channel
                voice = user['voice']

                if voice.get(str(member.guild.id)) is None:
                    voice[str(member.guild.id)] = {}

                voice[str(member.guild.id)]['voice_last_joined_ms'] = time_ms

                await self.bot.db.update_user(member.id, {'voice': voice})
            elif guild is not None and guild['afk_channel'] == after.channel.id:  # Moving to afk channel
                if user:
                    if user['voice'].get(str(member.guild.id)) is not None:
                        voice = user['voice']
                        if voice[str(member.guild.id)].get('voice_last_joined_ms', 0) != 0:
                            if voice[str(member.guild.id)].get('voice_time_spent_ms') is None:
                                voice[str(member.guild.id)]['voice_time_spent_ms'] = 0

                            voice[str(member.guild.id)]['voice_time_spent_ms'] += \
                                time_ms - voice[str(member.guild.id)]['voice_last_joined_ms']
                            voice[str(member.guild.id)]['voice_last_joined_ms'] = 0
                            await self.bot.db.update_user(member.id, {'voice': voice})


def setup(bot):
    bot.add_cog(LogEvents(bot))
