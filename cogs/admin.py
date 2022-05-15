import ast
import asyncio
import copy
import discord
import subprocess
import traceback
import typing

from discord.ext import commands
from utils.checks import access_level, AccessLevel, access_level_check


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = set()
        self._last_result = None

    async def cog_check(self, ctx):
        return await access_level_check(ctx, AccessLevel.TRUSTED)  # Minimum access level to use this cog

    # Below is from a previous version of https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py
    async def run_process(self, command: str) -> list[str]:
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

    def cleanup_code(self, content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, e: SyntaxError) -> str:
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    def insert_returns(self, body):
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])

        if isinstance(body[-1], ast.If):
            self.insert_returns(body[-1].body)
            self.insert_returns(body[-1].orelse)

        if isinstance(body[-1], ast.With):
            self.insert_returns(body[-1].body)

    @commands.command()
    @access_level(AccessLevel.ADMIN)
    async def eval(self, ctx, *, cmd):
        fn_name = "_eval_expr"

        if cmd.startswith("```") and cmd.endswith("```"):
            cmd = cmd[3:-3]
        elif cmd.startswith("`") and cmd.endswith("`"):
            cmd = cmd[1:-1]

        cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

        body = f"async def {fn_name}():\n{cmd}"

        parsed = ast.parse(body)
        body = parsed.body[0].body

        self.insert_returns(body)

        env = {
            'bot': ctx.bot,
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            'asyncio': asyncio,
            '__import__': __import__
        }

        exec(compile(parsed, filename="<ast>", mode="exec"), env)

        ret = await eval(f"{fn_name}()", env)
        await ctx.send(ret)

    @commands.command()
    @access_level(AccessLevel.ADMIN)
    async def sudo(
            self,
            ctx,
            channel: typing.Optional[discord.TextChannel],
            who: typing.Union[discord.Member, discord.User],
            *,
            command: str,
    ):
        """Run a command as another user optionally in another channel."""
        msg = copy.copy(ctx.message)
        new_channel = channel or ctx.channel
        msg.channel = new_channel
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command()
    @access_level(AccessLevel.ADMIN)
    async def sh(self, ctx, *, command: str):
        """Run a shell command."""
        async with ctx.typing():
            stdout, stderr = await self.run_process(command)

        if stderr:
            text = f'stdout:\n{stdout}\n\nstderr:\n{stderr}'
        else:
            text = stdout

        if len(text) > 2000:
            text = text[:2000]

        await ctx.send(text)  # do pagination later


def setup(bot):
    bot.add_cog(Admin(bot))
