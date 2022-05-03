import asyncpg
import json
import logging
import os
import typing
import pytz

from datetime import datetime


class DBException(Exception):
    pass


class BaseDBConnection:
    def __init__(self, host, db_name, user):
        self.host = host
        self.db_name = db_name
        self.user = user

    async def create_conn(self):
        conn = await asyncpg.connect(
            user=self.user,
            password=os.environ.get('ZOTE_DB_PASSWORD'),
            database=self.db_name,
            host=self.host
        )

        return conn


class DBConnection(BaseDBConnection):
    def __init__(self):
        super().__init__('192.168.0.129', 'wynndb', 'zote')
        self.guild_cache = {}
        logger = logging.getLogger('zote.database')
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

    # Guilds

    async def get_guild(self, guild_id: int) -> typing.Optional[asyncpg.Record]:
        """Get guild by id"""
        conn = await self.create_conn()

        if e := self.guild_cache.get(guild_id):
            return e

        query = 'SELECT * FROM zotebot.guilds WHERE id = $1'

        res = await conn.fetchrow(query, guild_id)
        await conn.close()

        if res:
            res = dict(res)
            res['rolemenu'] = json.loads(res['rolemenu'])

        self.guild_cache[guild_id] = res
        return res

    async def update_guild(self, guild_id: int, data: dict):
        """Update guild"""
        conn = await self.create_conn()

        d = ''
        n = 2
        values = []
        for key, value in data.items():
            d += f'{key} = ${n}, '

            if isinstance(value, dict):
                value = json.dumps(value)
            values.append(value)
            n += 1

        query = '''
        UPDATE zotebot.guilds
            SET {}
            WHERE id = $1
        '''.format(d[:-2])

        await conn.execute(query, guild_id, *values)
        await conn.close()

        if self.guild_cache.get(guild_id):
            self.guild_cache[guild_id].update(data)

    async def new_guild(self, guild_id: int):
        """New guild in database"""
        conn = await self.create_conn()

        query = '''
        INSERT INTO zotebot.guilds (id)
            VALUES ($1)
        '''

        await conn.execute(
            query, guild_id)
        await conn.close()

    def clear_cache(self):
        """Clear cache"""
        self.guild_cache = {}

    # Users

    async def get_user(self, user_id: int) -> typing.Optional[dict]:
        """Get user by id"""
        conn = await self.create_conn()

        query = 'SELECT * FROM zotebot.users WHERE id = $1'

        res = await conn.fetchrow(query, user_id)
        await conn.close()

        if res:
            res = dict(res)
            res['voice'] = json.loads(res['voice'])

        return res

    async def update_user(self, user_id: int, data: dict):
        """Update user value"""
        conn = await self.create_conn()

        d = ''
        n = 2
        values = []
        for key, value in data.items():
            d += f'{key} = ${n}, '

            if isinstance(value, dict):
                value = json.dumps(value)
            values.append(value)
            n += 1

        query = '''
        UPDATE zotebot.users
            SET {}
            WHERE id = $1
        '''.format(d[:-2])

        await conn.execute(query, user_id, *values)
        await conn.close()

    async def new_user(self, user_id: int):
        """Set user in database"""
        conn = await self.create_conn()

        query = '''
        INSERT INTO zotebot.users
            VALUES ($1)
        '''

        await conn.execute(
            query, user_id)
        await conn.close()

    async def get_top_voice_times(self, guild_id: int, limit: int = 10) -> typing.List[typing.Tuple[int, int]]:
        """Get top voice times"""
        conn = await self.create_conn()

        query = '''
            SELECT id, voice FROM zotebot.users
        '''

        guild_users = []

        res = await conn.fetch(query)
        await conn.close()

        for x in res:
            v = json.loads(x['voice'])
            if v.get(str(guild_id)) and v.get(str(guild_id)).get('voice_time_spent_ms', 0) != 0:
                guild_users.append((x['id'], v[str(guild_id)]))

        guild_users.sort(key=lambda u: u[1]['voice_time_spent_ms'], reverse=True)
        if len(guild_users) > limit:
            guild_users = guild_users[:limit]

        return guild_users

    # Utils

    async def get_time(self, guild_id: int) -> str:
        """Get timezone for guild"""
        v = await self.get_guild(guild_id)
        tz: str
        if v:
            tz = v.get('timezone', 'UTC')
        else:
            tz = 'UTC'

        now = datetime.now(pytz.timezone(tz))
        offset = now.strftime('%z')
        sign = offset[0]
        offset = int(offset[1:].strip('0') or '0')  # May not work correctly with +/-x:30 offsets
        return now.strftime('`[%H:%M:%S UTC{}{:01}]`'.format(sign, offset))
