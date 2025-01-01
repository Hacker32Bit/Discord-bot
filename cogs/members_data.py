import os
from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from dotenv import load_dotenv

load_dotenv()
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS members(user_id INTEGER, guild_id INTEGER, name TEXT, surname TEXT, 
                gender INTEGER, birthday TEXT, info TEXT, invites TEXT, invited_from TEXT)""")


class MembersData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Members Data\" cog is ready!")

    @app_commands.command(name="about_me", description="Tell me about you :)")
    @app_commands.choices(gender=[
        app_commands.Choice(name='Male', value=1),
        app_commands.Choice(name='Female', value=0),
    ])
    @app_commands.describe(name="What is your name?")
    @app_commands.describe(surname="What is your surname?")
    @app_commands.describe(gender="Select your gender")
    @app_commands.describe(birthday="Date of Birth. Type in format 'yyyy-mm-dd'. That was secret :)")
    async def rank_card_setting(self, interaction: discord.Interaction, name: str = None, surname: str = None,
                                birthday: str = None, gender: app_commands.Choice[int] = 0):
        pass


async def setup(bot):
    await bot.add_cog(MembersData(bot), guilds=[discord.Object(id=GUILD_ID)])
