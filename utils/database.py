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
        self.conn: typing.Optional[asyncpg.Connection] = None
        self.host = host
        self.db_name = db_name
        self.user = user

    async def connect(self):
        """Do not re-implement in child classes"""
        if self.conn:
            raise DBException(f'Connection to database {self.db_name} already established.')

        self.conn = await asyncpg.connect(
            user=self.user,
            password=os.environ.get('ZOTE_DB_PASSWORD'),
            database=self.db_name,
            host=self.host
        )

    async def close(self):
        """Do not re-implement in child classes"""
        if not self.conn:
            raise DBException(f'Connection to database {self.db_name} does not exist.')

        await self.conn.close()
        self.conn = None

    @property
    def is_connected(self):
        return bool(self.conn)


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
        if not self.is_connected:
            await self.connect()

        if e := self.guild_cache.get(guild_id):
            return e

        query = 'SELECT * FROM zotebot.guilds WHERE id = $1'

        return await self.conn.fetchrow(query, guild_id)

    async def update_guild(self, guild_id: int, data: dict):
        """Update guild"""
        if not self.is_connected:
            await self.connect()

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

        await self.conn.execute(query, guild_id, *values)

        if self.guild_cache.get(guild_id):
            self.guild_cache[guild_id].update(data)

    async def new_guild(self, guild_id: int):
        """New guild in database"""
        if not self.is_connected:
            await self.connect()

        query = '''
        INSERT INTO zotebot.guilds (id)
            VALUES ($1)
        '''

        await self.conn.execute(
            query, guild_id)

    def clear_cache(self):
        """Clear cache"""
        self.guild_cache = {}

    # Users

    async def get_user(self, user_id: int) -> typing.Optional[dict]:
        """Get user by id"""
        if not self.is_connected:
            await self.connect()

        query = 'SELECT * FROM zotebot.users WHERE id = $1'

        res = await self.conn.fetchrow(query, user_id)
        if res:
            res = dict(res)
            res['voice'] = json.loads(res['voice'])

        return res

    async def update_user(self, user_id: int, data: dict):
        """Update user value"""
        if not self.is_connected:
            await self.connect()

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

        await self.conn.execute(query, user_id, *values)

    async def new_user(self, user_id: int):
        """Set user in database"""
        if not self.is_connected:
            await self.connect()

        query = '''
        INSERT INTO zotebot.users
            VALUES ($1)
        '''

        await self.conn.execute(
            query, user_id)

    async def get_top_voice_times(self, guild_id: int, limit: int = 10) -> typing.List[typing.Tuple[int, int]]:
        """Get top voice times"""
        if not self.is_connected:
            await self.connect()

        query = '''
            SELECT id, voice FROM zotebot.users
        '''

        guild_users = []
        res = await self.conn.fetch(query)
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
