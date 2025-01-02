import json
import os
from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from dotenv import load_dotenv
from dateutil.parser import parse
import phonenumbers
from email_validator import validate_email, EmailNotValidError


load_dotenv()
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS members (user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, name TEXT, 
surname TEXT, gender INTEGER, birthday TEXT, country TEXT, languages TEXT, info TEXT, phone TEXT, email TEXT, 
invites TEXT, invited_from TEXT, admin_info TEXT, PRIMARY KEY("user_id"));""")

cursor.execute("""CREATE TABLE IF NOT EXISTS members_privacy (user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, 
name INTEGER NOT NULL DEFAULT 1, surname INTEGER NOT NULL DEFAULT 1, gender INTEGER NOT NULL DEFAULT 1, 
birthday INTEGER NOT NULL DEFAULT 0, country INTEGER NOT NULL DEFAULT 1, languages INTEGER NOT NULL DEFAULT 1, 
info INTEGER NOT NULL DEFAULT 1, phone INTEGER NOT NULL DEFAULT 0, email INTEGER NOT NULL DEFAULT 0, 
PRIMARY KEY("user_id"));""")


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
    @app_commands.describe(country="Enter ONE your country name in ISO 3166-1 code. (AD, AE, ..., ZM, ZW) Example: DE")
    @app_commands.describe(
        languages="Enter yours languages list in ISO 639-1 code. (ad, ae, ..., zh, zu) Example: en, en-US, ru, zh")
    @app_commands.describe(info="Enter about you small info (MAX 4000 symbols)")
    @app_commands.describe(phone="[Private] Enter your phone")
    @app_commands.describe(email="[Private] Enter your email")
    async def about_update(self, interaction: discord.Interaction, name: str = None, surname: str = None,
                           gender: app_commands.Choice[int] = 0, birthday: str = None, country: str = None,
                           languages: str = None, info: str = None, phone: str = None, email: str = None):
        # Collect errors messages on validate state
        err_messages: str = ""

        # name validation [1, 35] symbols
        if name and len(name) > 35:
            err_messages += "Too long name. Name should be contains [1, 35] letters.\n"

        # surname validation valid [1, 35] symbols
        if surname and len(surname) > 35:
            err_messages += "Too long surname. Surname should be contains [1, 35] letters.\n"

        # birthday validation. Parser can parse a lot of variants from str
        date = ""
        if birthday:
            try:
                date = parse(birthday, fuzzy=False).date()
            except ValueError as err:
                err_messages += str(err)

        # country validation from countries_list.json
        if country:
            with open('assets/jsons/countries_list.json', 'r') as file:
                countries_dict = json.load(file)
                if country.upper() not in countries_dict:
                    err_messages += f"Country '{country}' does not exist in ISO 3166-1 codes list.\n"
                    country = None

        # languages validation from languages_dict.json
        if languages:
            with open('assets/jsons/languages_list.json', 'r') as file:
                languages_dict = json.load(file)
                languages_list = languages.strip().lower().split(",")
                languages = ""
                if len(languages_list):
                    for lang in languages_list:
                        if lang in languages_dict:
                            languages += f"{lang}, "
                        else:
                            err_messages += f"Language '{lang}' does not exist in ISO 639-1 codes list."
                if not languages:
                    err_messages += f"From '{languages}' not found at least 1 languages in ISO 639-1 code.\n"
                    languages = None
                else:
                    languages = languages[:-2]

        # phone validation
        if phone:
            phone_number = phonenumbers.parse(phone)
            valid = phonenumbers.is_valid_number(phone_number)
            print(phone_number, valid)

        # email validation
        if email:
            try:
                # Check that the email address is valid. Turn on check_deliverability
                # for first-time validations like on account creation pages (but not
                # login pages).
                email_info = validate_email(email, check_deliverability=True)

                # After this point, use only the normalized form of the email address,
                # especially before going to a database query.
                email = email_info.normalized
                print(email_info, email)
            except EmailNotValidError as e:
                # The exception message is human-readable explanation of why it's
                # not a valid (or deliverable) email address.
                print(str(e))

        # Return when have incorrect inputs. Else continues.
        if len(err_messages):
            await interaction.response.send_message(err_messages)  # NOQA
        else:
            # Everything good.

            # Fetch member data from db.
            cursor.execute(f"SELECT user_id, guild_id, name, surname, gender, birthday, country, languages, info, "
                           f"phone, email FROM members "
                           f"WHERE user_id = {interaction.user.id} AND guild_id = {interaction.guild.id}")
            result = cursor.fetchone()

            # Data for only exist keys and values for db query
            data = {"name": name, "surname": surname, "gender": gender.value, "birthday": date, "country": country,
                    "languages": languages, "info": info, "phone": phone, "email": email}

            # If first time. Insert
            if result is None:
                exist_keys = ""
                keys_values = ""
                for key in data.keys():
                    if data[key]:
                        exist_keys += f"{str(key)}, "
                        keys_values += f"'{str(data[key])}', "

                print(type(data), data)
                print(f"|{exist_keys}|")
                print(f"|{keys_values}|")

                cursor.execute(f"INSERT INTO members_privacy(user_id, guild_id) "
                               f"VALUES({interaction.user.id}, {interaction.guild.id})")
                database.commit()

                cursor.execute(f"INSERT INTO members(user_id, guild_id, {exist_keys[:-2]}) "
                               f"VALUES({interaction.user.id}, {interaction.guild.id}, {keys_values[:-2]})")
                database.commit()
            else:
                (user_id, guild_id, old_name, old_surname, old_gender, old_birthday, old_country, old_languages,
                 old_info,
                 old_phone, old_email) = result

                print(type(result), result)
                print(user_id, guild_id, old_name, old_surname, old_gender, old_birthday, old_country, old_languages,
                      old_info, old_phone, old_email)

                # is_admin for access edit everything
                is_admin = discord.utils.get(interaction.guild.roles, name="Admin") in interaction.user.roles

                # Unchangeable variables when not admin and already exist
                if old_name and not is_admin:
                    data["name"] = None
                if old_surname and not is_admin:
                    data["surname"] = None
                if old_birthday and not is_admin:
                    data["birthday"] = None
                if old_gender and not is_admin:
                    data["gender"] = None

                query = ""
                for key in data.keys():
                    if data[key]:
                        query += f"{str(key)} = '{str(data[key])}', "

                print(f"|{query[:-2]}|")
                cursor.execute(f"UPDATE members SET {query[:-2]} WHERE user_id = {interaction.user.id} "
                               f"AND guild_id = {interaction.guild.id}")
                database.commit()

            await interaction.response.send_message("Thanks for sharing information about you!")  # NOQA


async def setup(bot):
    await bot.add_cog(MembersData(bot), guilds=[discord.Object(id=GUILD_ID)])
