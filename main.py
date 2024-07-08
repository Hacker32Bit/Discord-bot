import discord
from discord.ext import commands
from typing import Final
from dotenv import load_dotenv
import os
import logging

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode="a")

load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
APPLICATION_ID: Final[str] = os.getenv("APPLICATION_ID")

# Bot setup
intents: discord.Intents = discord.Intents.default()
intents.message_content = True  # NOQA
intents.members = True  # NOQA
intents.voice_states = True # NOQA
intents.guilds = True # NOQA
intents.presences = True # NOQA

client = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)


async def load_cogs():
    for filename in os.listdir("./cogs"):
        try:
            if filename.endswith(".py"):
                await client.load_extension(f"cogs.{filename[:-3]}")
        except Exception as err:
            print(f'Failed to load {filename} cog: {err}')


@client.event
async def on_ready():
    await load_cogs()
    print('We have logged in as {0.user}'.format(client))


if __name__ == "__main__":
    try:
        client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
    except discord.HTTPException as e:
        if e.status == 429:
            print("The Discord servers denied the connection for making too many requests")
        else:
            raise e
