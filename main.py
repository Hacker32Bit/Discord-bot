import asyncio
import os
import logging
from time import strftime

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")

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
    print(f'Logged in as {client.user} (ID: {client.user.id})')

async def main():
    try:
        await load_extensions()
        log_dir = os.path.join(os.sep, "tmp", "logs")
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(
            filename=os.path.join(log_dir, f"{strftime('%Y-%m-%d %H:%M:%S')}.log"),
            encoding='utf-8',
            mode="a")
        discord.utils.setup_logging(level=logging.INFO, root=False, handler=handler)
        await client.start(TOKEN)
    except discord.HTTPException as e:
        if e.status == 429:
            print("Rate limited by Discord (429)")
        else:
            raise e

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Received Ctrl+C, exiting.")
