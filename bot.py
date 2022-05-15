import discord
import logging
import os

from discord.ext import commands
from utils.database import DBConnection
from utils.utils import aloc


class ZoteBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = DBConnection()
        self._watcher_mode = os.environ.get('WATCHER_MODE', "0") == "1"

    async def close(self):
        if self.db.is_connected:
            await self.db.close()

        await super().close()

    async def on_message(self, message):
        if not self._watcher_mode:
            await self.process_commands(message)

    async def on_ready(self):
        await self.db.connect()
        logger.debug(f'Logged in as {bot.user} ({bot.user.id})')
        logger.debug(f'All lines of code: {aloc()}')


if __name__ == '__main__':
    logger = logging.getLogger(
        'zote' if os.environ.get('DEBUG', "0") == "0"
        else 'purple'
    )
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    bot = ZoteBot(command_prefix='>', intents=discord.Intents.all())

    for filename in os.listdir('cogs'):
        if filename.endswith('.py'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
            except commands.ExtensionError as e:
                logger.error(e)

    bot.run(
        os.environ.get('ZOTE_DISCORD_TOKEN', 'abcdefg1234567') if os.environ.get('DEBUG', "0") == "0"
        else os.environ.get('PURPLE_DISCORD_TOKEN', 'abcdefg1234567')
    )
