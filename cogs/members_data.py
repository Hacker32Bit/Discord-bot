import io
import os
import re
import time
from typing import Final
import discord
from discord.ext import commands
import math
import sqlite3
from dotenv import load_dotenv

load_dotenv()
GENERAL_TEXT_CHANNEL_ID: Final[str] = os.getenv("GENERAL_TEXT_CHANNEL_ID")
GENERAL_VOICE_CHANNEL_ID: Final[str] = os.getenv("GENERAL_VOICE_CHANNEL_ID")
STREAMS_VOICE_CHANNEL_ID: Final[str] = os.getenv("STREAMS_VOICE_CHANNEL_ID")
MUSIC_VOICE_CHANNEL_ID: Final[str] = os.getenv("MUSIC_VOICE_CHANNEL_ID")
AFK_VOICE_CHANNEL_ID: Final[str] = os.getenv("AFK_VOICE_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS members(user_id INTEGER, guild_id INTEGER, name TEXT, surname TEXT, 
                birthday TEXT, info TEXT)""")


class MembersData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Members Data\" cog is ready!")


async def setup(bot):
    await bot.add_cog(MembersData(bot), guilds=[discord.Object(id=GUILD_ID)])
