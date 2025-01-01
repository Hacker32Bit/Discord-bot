import os
from datetime import datetime
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

cursor.execute("""CREATE TABLE IF NOT EXISTS members(user_id INTEGER, guild_id INTEGER, name TEXT, surname TEXT, gender 
                INTEGER, birthday TEXT, region TEXT, languages TEXT, info TEXT, invites TEXT, invited_from TEXT)""")


class MembersData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Members Data\" cog is ready!")

    # Add info about Member
    @app_commands.command(name="about_me", description="Tell me about you :)")
    @app_commands.choices(gender=[
        app_commands.Choice(name='Male', value=1),
        app_commands.Choice(name='Female', value=2),
        app_commands.Choice(name='Other', value=-1),
    ])
    @app_commands.describe(name="What is your name?")
    @app_commands.describe(surname="What is your surname?")
    @app_commands.describe(gender="Select your gender")
    @app_commands.describe(birthday="Date of Birth. Type in format 'dd-mm-yyyy'. That was secret :)")
    async def about_me(self, interaction: discord.Interaction, name: str = None, surname: str = None,
                       birthday: str = None, gender: app_commands.Choice[int] = 0):

        err_messages: str = ""

        if name and len(name) > 35:
            err_messages += "Too long name. Name should be contains [1, 35] letters.\n"

        if surname and len(surname) > 35:
            err_messages += "Too long surname. Surname should be contains [1, 35] letters.\n"

        date = ""
        if birthday:
            try:
                date = datetime.strptime(birthday, '%d-%m-%Y').date()
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

            cursor.execute(f"SELECT * FROM members WHERE user_id = {interaction.user.id} AND "
                           f"guild_id = {interaction.guild.id}")
            result = cursor.fetchone()

            (user_id, guild_id, old_name, old_surname, old_gender,
             old_birthday, old_region, old_languages, old_info) = result

            print(type(result), result)
            print(user_id, guild_id, old_name, old_surname, old_gender, old_birthday, old_region, old_languages,
                  old_info)

            if result is None:
                cursor.execute(f"INSERT INTO members(user_id, guild_id, {exist_keys[:-2]}) "
                               f"VALUES({interaction.user.id}, {interaction.guild.id}, {keys_values[:-2]})")
                database.commit()

            await interaction.response.send_message("Thanks for sharing information, about you!")  # NOQA


async def setup(bot):
    await bot.add_cog(MembersData(bot), guilds=[discord.Object(id=GUILD_ID)])
