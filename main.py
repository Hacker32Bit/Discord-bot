import discord
from discord.ext import commands
from typing import Final
from dotenv import load_dotenv
import os
import asyncio


load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
APPLICATION_ID: Final[str] = os.getenv("APPLICATION_ID")

# Bot setup
intents: discord.Intents = discord.Intents.default()
intents.message_content = True  # NOQA
intents.members = True  # NOQA

client = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)


@client.event
async def on_ready():
    print("[INFO] Success: Bot is connected to Discord!")


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with client:
        await load()
        await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

