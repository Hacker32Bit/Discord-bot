import os
from datetime import datetime
from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from dotenv import load_dotenv
from dateutil.parser import parse

load_dotenv()
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS members (user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, name TEXT, 
surname TEXT, gender INTEGER, birthday TEXT, region TEXT, languages TEXT, info TEXT, phone TEXT, email TEXT, 
invites TEXT, invited_from TEXT, admin_info TEXT);""")

cursor.execute("""CREATE TABLE IF NOT EXISTS members_privacy (user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, 
name INTEGER NOT NULL DEFAULT 1, surname INTEGER NOT NULL DEFAULT 1, gender INTEGER NOT NULL DEFAULT 1, 
birthday INTEGER NOT NULL DEFAULT 0, region INTEGER NOT NULL DEFAULT 1, languages INTEGER NOT NULL DEFAULT 1, 
info INTEGER NOT NULL DEFAULT 1, phone INTEGER NOT NULL DEFAULT 0, email INTEGER NOT NULL DEFAULT 0);""")


class MembersData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Members Data\" cog is ready!")

    # Add info about Member
    @app_commands.command(name="about_update", description="Add/Update information about you. [Private] fields are "
                                                           "private by default for first input.")
    @app_commands.choices(gender=[
        app_commands.Choice(name='Male', value=1),
        app_commands.Choice(name='Female', value=2),
        app_commands.Choice(name='Other', value=-1),
    ])
    @app_commands.describe(name="What is your name?")
    @app_commands.describe(surname="What is your surname?")
    @app_commands.describe(gender="Select your gender")
    @app_commands.describe(birthday="[Private] Date of Birth. Type in this order: date, month, year.")
    @app_commands.describe(region="Enter your region name")
    @app_commands.describe(languages="Enter yours languages list")
    @app_commands.describe(info="Enter about you small info (MAX 4000 symbols)")
    @app_commands.describe(phone="[Private] Enter your phone")
    @app_commands.describe(email="[Private] Enter your email")
    async def about_update(self, interaction: discord.Interaction, name: str = None, surname: str = None,
                           gender: app_commands.Choice[int] = 0, birthday: str = None, region: str = None,
                           languages: str = None, info: str = None, phone: str = None, email: str = None):

        err_messages: str = ""

        if name and len(name) > 35:
            err_messages += "Too long name. Name should be contains [1, 35] letters.\n"

        if surname and len(surname) > 35:
            err_messages += "Too long surname. Surname should be contains [1, 35] letters.\n"

        date = ""
        if birthday:
            try:
                date = parse(birthday, fuzzy=False)
            except ValueError as err:
                err_messages += str(err)

        data = {"name": name, "surname": surname, "birthday": date, "gender": gender.value}
        exist_keys = ""
        keys_values = ""
        for key in data.keys():
            if data[key]:
                exist_keys += f"{str(key)}, "
                keys_values += f"'{str(data[key])}', "

        print(type(data), data)
        print(f"|{exist_keys}|")
        print(f"|{keys_values}|")

        if len(err_messages):
            await interaction.response.send_message(err_messages)  # NOQA
        else:

            cursor.execute(f"SELECT user_id, guild_id, name, surname, gender, birthday, region, languages, info, "
                           f"phone, email FROM members "
                           f"WHERE user_id = {interaction.user.id} AND guild_id = {interaction.guild.id}")
            result = cursor.fetchone()

            (user_id, guild_id, old_name, old_surname, old_gender, old_birthday, old_region, old_languages, old_info,
             old_phone, old_email) = result

            print(type(result), result)
            print(user_id, guild_id, old_name, old_surname, old_gender, old_birthday, old_region, old_languages,
                  old_info, old_phone, old_email)

            if result is None:
                cursor.execute(f"INSERT INTO members_privacy(user_id, guild_id) "
                               f"VALUES({interaction.user.id}, {interaction.guild.id})")
                database.commit()

                cursor.execute(f"INSERT INTO members(user_id, guild_id, {exist_keys[:-2]}) "
                               f"VALUES({interaction.user.id}, {interaction.guild.id}, {keys_values[:-2]})")
                database.commit()

            await interaction.response.send_message("Thanks for sharing information, about you!")  # NOQA


async def setup(bot):
    await bot.add_cog(MembersData(bot), guilds=[discord.Object(id=GUILD_ID)])
