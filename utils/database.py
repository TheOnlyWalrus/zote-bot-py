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
        self.pool: typing.Optional[asyncpg.pool.Pool] = None
        self.host = host
        self.db_name = db_name
        self.user = user

        # Setup logger
        logger = logging.getLogger('utils.database')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

    async def connect(self):
        if self.is_connected:
            return

        self.pool = await asyncpg.create_pool(  # Create a connection pool
            user=self.user,
            password=os.environ.get('DB_PASSWORD'),
            database=self.db_name,
            host=self.host
        )

    async def close(self):
        if not self.pool:
            self.logger.error(f'Connection pool for database {self.db_name} does not exist.')
            return

        await self.pool.close()
        self.pool = None

    @property
    def is_connected(self):
        return self.pool is not None


class DBConnection(BaseDBConnection):
    def __init__(self, bot):
        super().__init__('192.168.0.129', 'wynndb', 'zote')
        self.bot = bot
        self.guild_cache = {}
        self.schema_name = 'purple' if self.bot.debug_mode else 'zotebot'

    # Guilds

    async def get_guild(self, guild_id: int) -> typing.Optional[dict]:
        """Get guild by id"""
        await self.connect()  # Connect to database

        if e := self.guild_cache.get(guild_id):  # Check cache first
            return e

        async with self.pool.acquire() as conn:
            query = 'SELECT * FROM {}.guilds WHERE id = $1'.format(self.schema_name)
            res = await conn.fetchrow(query, guild_id)  # Fetch a guild row

        if res:  # if guild exists
            res = dict(res)  # Convert to dict
            res['rolemenu'] = json.loads(res['rolemenu'])  # Convert rolemenu to dict from json

        self.guild_cache[guild_id] = res  # Add to cache
        return res

    async def update_guild(self, guild_id: int, data: dict):
        """Update guild"""
        await self.connect()  # Connect to database

        qry = ''  # Set query to build
        n = 2  # Starting argument number
        values = []  # Values to pass to query

        for key, value in data.items():  # Cycle through data to update
            qry += f'{key} = ${n}, '  # Add to query

            if isinstance(value, dict):  # If value is dict, convert to json string
                value = json.dumps(value)

            values.append(value)  # Add to values
            n += 1  # Increment argument number

        async with self.pool.acquire() as conn:
            query = '''
            UPDATE {}.guilds
                SET {}
                WHERE id = $1
            '''.format(self.schema_name, qry[:-2])  # Create update query from qry and remove trailing comma

            await conn.execute(query, guild_id, *values)  # Update guild values

        if self.guild_cache.get(guild_id):  # If guild is in cache update it
            self.guild_cache[guild_id].update(data)

    async def new_guild(self, guild_id: int):
        """New guild in database"""
        await self.connect()  # Connect to database

        async with self.pool.acquire() as conn:
            query = '''
            INSERT INTO {}.guilds (id)
                VALUES ($1)
            '''.format(self.schema_name)

            await conn.execute(
                query, guild_id)  # Insert new guild

    def clear_cache(self):
        """Clear cache"""
        self.guild_cache = {}

    # Users

    async def get_user(self, user_id: int) -> typing.Optional[dict]:
        """Get user by id"""
        await self.connect()  # Connect to database

        async with self.pool.acquire() as conn:
            query = 'SELECT * FROM {}.users WHERE id = $1'.format(self.schema_name)

            res = await conn.fetchrow(query, user_id)  # Fetch user row

        if res:  # If user exists
            res = dict(res)  # Convert to dict
            res['voice'] = json.loads(res['voice'])  # Convert voice to dict from json

        return res

    async def update_user(self, user_id: int, data: dict):
        """Update user value"""
        await self.connect()

        qry = ''  # Set query to build
        n = 2  # Starting argument number
        values = []  # Values to pass to query

        for key, value in data.items():  # Cycle through data to update
            qry += f'{key} = ${n}, '  # Add to query

            if isinstance(value, dict):  # If value is dict, convert to json string
                value = json.dumps(value)

            values.append(value)  # Add to values
            n += 1  # Increment argument number

        async with self.pool.acquire() as conn:
            query = '''
            UPDATE {}.users
                SET {}
                WHERE id = $1
            '''.format(self.schema_name, qry[:-2])  # Create update query from qry and remove trailing comma

            await conn.execute(query, user_id, *values)  # Update user values

    async def new_user(self, user_id: int):
        """Set user in database"""
        await self.connect()  # Connect to database

        async with self.pool.acquire() as conn:
            query = '''
            INSERT INTO {}.users
                VALUES ($1)
            '''.format(self.schema_name)

            await conn.execute(
                query, user_id)  # Insert new user

    async def get_top_voice_times(self, guild_id: int, limit: int = 10) -> typing.List[typing.Tuple[int, int]]:
        """Get top voice times"""
        await self.connect()  # Connect to database

        async with self.pool.acquire() as conn:
            query = '''
                SELECT id, voice FROM {}.users
            '''.format(self.schema_name)

            res = await conn.fetch(query)  # Fetch all users

        guild_users = []  # List of users in this guild

        for x in res:  # for each user in the db
            v = json.loads(x['voice'])  # load void data
            if v.get(str(guild_id)) \
                    and v.get(str(guild_id)).get('voice_time_spent_ms', 0) != 0:
                # If user has voice data in this guild and has spent voice time, add to list
                guild_users.append((x['id'], v[str(guild_id)]))

        guild_users.sort(key=lambda u: u[1]['voice_time_spent_ms'], reverse=True)  # Sort by voice time
        if len(guild_users) > limit:
            guild_users = guild_users[:limit]  # Limit to given limit (default 10)

        return guild_users

    # Utils

    async def get_time(self, guild_id: int) -> str:
        """Get timezone for guild"""
        guild = await self.get_guild(guild_id)
        tz: str

        # Get timezone from guild, or default to UTC
        if guild:
            tz = guild.get('timezone', 'UTC')
        else:
            tz = 'UTC'

        now = datetime.now(pytz.timezone(tz))  # Get current time in guild timezone
        offset = now.strftime('%z')  # Get timezone offset
        sign = offset[0]  # Get sign of offset
        offset = int(offset[1:].strip('0') or '0')  # May not work correctly with +/-x:30 offsets
        return now.strftime('`[%H:%M:%S UTC{}{:01}]`'.format(sign, offset))  # Return formatted time
