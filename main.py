import asyncio
import os
import sys
import logging
from time import strftime
from typing import Final

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
APPLICATION_ID: Final[str] = os.getenv("APPLICATION_ID")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.presences = True

client = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)

async def load_extensions():
    cogs_path = os.path.join(os.path.dirname(__file__), "cogs")
    if not os.path.isdir(cogs_path):
        print(f"[ERROR] Cogs directory not found: {cogs_path}")
        return
    for filename in os.listdir(cogs_path):
        if filename.endswith(".py"):
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
            except Exception as err:
                print(f"Failed to load {filename}: {err}")

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

async def main():
    await load_extensions()

    log_path = os.path.join(os.sep, "tmp", "logs", f"{strftime('%Y-%m-%d %H:%M:%S')}.log")
    handler = logging.FileHandler(filename=log_path, encoding='utf-8', mode="a")
    discord.utils.setup_logging(level=logging.DEBUG, root=False, handler=handler)

    try:
        await client.start(TOKEN)
    except discord.HTTPException as e:
        if e.status == 429:
            print("The Discord servers denied the connection for making too many requests")
        else:
            raise
    except asyncio.CancelledError:
        print("Bot shutdown was cancelled.")
    finally:
        if not client.is_closed():
            await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Received Ctrl+C. Exiting cleanly...")
