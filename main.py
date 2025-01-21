import asyncio
import sys

import discord
from discord.ext import commands
from typing import Final
from dotenv import load_dotenv
import os
import logging
from time import strftime

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
APPLICATION_ID: Final[str] = os.getenv("APPLICATION_ID")

# Bot setup
intents: discord.Intents = discord.Intents.default()
intents.message_content = True  # NOQA
intents.members = True  # NOQA
intents.voice_states = True  # NOQA
intents.guilds = True  # NOQA
intents.presences = True  # NOQA

client = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)


async def load_extensions():
    for filename in os.listdir("./cogs"):
        try:
            if filename.endswith(".py"):
                await client.load_extension(f"cogs.{filename[:-3]}")
        except Exception as err:
            print(f'Failed to load {filename} cog: {err}')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


async def main():
    try:
        await load_extensions()
        handler = logging.FileHandler(
            filename=os.path.join(os.sep, "tmp", "logs", f"{strftime('%Y-%m-%d %H:%M:%S')}.log"),
            encoding='utf-8',
            mode="a")
        discord.utils.setup_logging(level=logging.DEBUG, root=False, handler=handler)
        await client.start(TOKEN)

    except discord.HTTPException as e:
        if e.status == 429:
            print("The Discord servers denied the connection for making too many requests")
        else:
            raise e


if __name__ == "__main__":
    asyncio.run(main())
    # try:
    #     loop = asyncio.get_event_loop()
    #     loop.run_until_complete(main())
    # except KeyboardInterrupt:
    #     print("Received Ctrl+C. Stopping gracefully...")
    #     # Cancel all running tasks
    #     for task in asyncio.Task.all_tasks():
    #         task.cancel()
    #     # Optionally: Close any open resources (sockets, files, etc.)
    #     # Cleanup code here
    # finally:
    #     loop.close()
