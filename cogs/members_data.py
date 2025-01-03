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
    @staticmethod
    async def about_update_function(interaction: discord.Interaction, name: str = None, surname: str = None,
                                    gender: app_commands.Choice[int] = 0, birthday: str = None, country: str = None,
                                    languages: str = None, info: str = None, phone: str = None, email: str = None,
                                    is_admin: bool = False, mention: discord.Member = None):
        # Set user_id from Interaction or from mention(If admin)
        user_id = interaction.user.id
        if mention:
            user_id = mention.id

        # Collect errors messages on validate state
        err_messages: str = ""

        # name validation [1, 35] symbols
        if name and len(name) > 35:
            name = None
            err_messages += "Too long name. Name should be contains [1, 35] letters.\n"

        # surname validation valid [1, 35] symbols
        if surname and len(surname) > 35:
            surname = None
            err_messages += "Too long surname. Surname should be contains [1, 35] letters.\n"

        # birthday validation. Parser can parse a lot of variants from str
        date = None
        if birthday:
            try:
                date = str(parse(birthday, fuzzy=False).date())
            except ValueError as err:
                err_messages += f"{str(err)}\n"

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
                languages_list = languages.replace(" ", "").lower().split(",")
                languages = ""
                if len(languages_list):
                    lang_err = ""
                    for lang in languages_list:
                        if lang in languages_dict:
                            languages += f"{lang}, "
                        else:
                            lang_err += f"{lang}, "
                    if lang_err:
                        err_messages += f"Language(s) '{lang_err[:-2]}' does not exist in ISO 639-1 codes list.\n"
                if not languages:
                    languages = None
                    err_messages += f"From '{languages}' not found at least 1 languages in ISO 639-1 code.\n"
                else:
                    languages = languages[:-2]

        # info validation
        if info and len(info) > 4000:
            info = info[:4000]
            err_messages += f"Your info is too long. It was automatically shortened to 4,000 characters"

        # phone validation
        if phone:
            try:
                phone_number = phonenumbers.parse(phone)
                valid = phonenumbers.is_valid_number(phone_number)
                print(phone_number, valid)
            except phonenumbers.NumberParseException as err:
                phone = None
                err_messages += f"Phone argument error: {str(err)}\n"

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
            except EmailNotValidError as err:
                # The exception message is human-readable explanation of why it's
                # not a valid (or deliverable) email address.
                email = None
                err_messages += f"{str(err)}\n"

        # Everything good.

        # Fetch member data from db.
        cursor.execute(f"SELECT user_id, guild_id, name, surname, gender, birthday, country, languages, info, "
                       f"phone, email FROM members "
                       f"WHERE user_id = {user_id} AND guild_id = {interaction.guild.id}")
        result = cursor.fetchone()

        # Data for only exist keys and values for db query
        data = {"name": name, "surname": surname, "gender": gender.value if gender else None, "birthday": date,
                "country": country, "languages": languages, "info": info, "phone": phone, "email": email}

        print("Initial data: ", data)

        # If first time. Insert
        if result is None:
            exist_keys = ""
            keys_values = []
            for key in data.keys():
                if data[key]:
                    exist_keys += f"{str(key)}, "
                    keys_values.append(str(data[key]))

            print("result is None")
            print("exist_keys: ", exist_keys)
            print("keys_values: ", keys_values)

            if exist_keys:
                cursor.execute(f"INSERT INTO members_privacy(user_id, guild_id) "
                               f"VALUES({user_id}, {interaction.guild.id})")
                database.commit()

                cursor.execute(f"INSERT INTO members(user_id, guild_id, {exist_keys[:-2]}) VALUES( "
                               f"{user_id}, {interaction.guild.id}, {'?, ' * len(keys_values)[:-2]})",
                               tuple(keys_values))
                database.commit()
        else:
            (user_id, guild_id, old_name, old_surname, old_gender, old_birthday, old_country, old_languages,
             old_info, old_phone, old_email) = result

            print("result", result)

            # Unchangeable variables when not admin and already exist
            if old_name and not is_admin:
                data["name"] = None
            if old_surname and not is_admin:
                data["surname"] = None
            if old_birthday and not is_admin:
                data["birthday"] = None
            if old_gender and not is_admin:
                data["gender"] = None

            print("data after changes: ", data)

            exist_keys = ""
            keys_values = []
            for key in data.keys():
                if data[key]:
                    exist_keys += f"{str(key)} = ?, "
                    keys_values.append(str(data[key]))

            print("Result is exist")
            print("exist_keys: ", exist_keys)
            print("keys_values: ", keys_values)

            if len(keys_values):
                cursor.execute(f"UPDATE members SET {exist_keys[:-2]} WHERE user_id = {user_id} "
                               f"AND guild_id = {interaction.guild.id}", tuple(keys_values))
                database.commit()

        response_message = "Thanks for sharing information about you!"
        if len(err_messages):
            response_message += f" But I was ignored this errors:\n{err_messages}"

        await interaction.response.send_message(response_message)  # NOQA

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
    @app_commands.describe(birthday="[Private] date of birth. Type in this order: date, month, year.")
    @app_commands.describe(country="Enter ONE your country name in ISO 3166-1 code. (AD, AE, ..., ZM, ZW) Example: DE")
    @app_commands.describe(
        languages="Enter yours languages list in ISO 639-1 code. (ad, ae, ..., zh, zu) Example: en, en-US, ru, zh")
    @app_commands.describe(info="Enter about you small info (MAX 4000 symbols)")
    @app_commands.describe(phone="[Private] Enter your phone in E.164 format. Example: +14155552671")
    @app_commands.describe(email="[Private] Enter your email in RFC 6530 standard. Example: local-part@domain.com")
    async def about_update(self, interaction: discord.Interaction, name: str = None, surname: str = None,
                           gender: app_commands.Choice[int] = 0, birthday: str = None, country: str = None,
                           languages: str = None, info: str = None, phone: str = None, email: str = None):
        # is_admin for access edit everything
        is_admin = discord.utils.get(interaction.guild.roles, name="Admin") in interaction.user.roles
        await self.about_update_function(interaction, name, surname, gender, birthday, country, languages, info, phone,
                                         email, is_admin)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="about_update_mention", description="[ADMIN] Add/Update information about member.")
    @app_commands.choices(gender=[
        app_commands.Choice(name='Male', value=1),
        app_commands.Choice(name='Female', value=2),
        app_commands.Choice(name='Other', value=-1),
    ])
    @app_commands.describe(mention="Member mention. Example: @Hacker32Bit")
    @app_commands.describe(name="Member name")
    @app_commands.describe(surname="Member surname")
    @app_commands.describe(gender="Member gender")
    @app_commands.describe(birthday="Member date of birth. Type in this order: date, month, year.")
    @app_commands.describe(
        country="Enter member ONE country name in ISO 3166-1 code. (AD, AE, ..., ZM, ZW) Example: DE")
    @app_commands.describe(
        languages="Enter member languages list in ISO 639-1 code. (ad, ae, ..., zh, zu) Example: en, en-US, ru, zh")
    @app_commands.describe(info="Enter member small info (MAX 4000 symbols)")
    @app_commands.describe(phone="Enter member phone in E.164 format. Example: +14155552671")
    @app_commands.describe(email="Enter member email in RFC 6530 standard. Example: local-part@domain.com")
    async def about_update_mention(self, interaction: discord.Interaction, mention: discord.Member, name: str = None,
                                   surname: str = None,
                                   gender: app_commands.Choice[int] = 0, birthday: str = None, country: str = None,
                                   languages: str = None, info: str = None, phone: str = None, email: str = None):
        await self.about_update_function(interaction, name, surname, gender, birthday, country, languages, info, phone,
                                         email, True, mention)

    @staticmethod
    async def show_info(interaction: discord.Interaction, mention: discord.Member = None,
                        show_private: bool = False, force_private: bool = False) -> None:

        print(type(interaction.user), interaction.user)
        print(type(mention), mention)
        print(type(show_private), show_private)
        print(type(force_private), force_private)
        await interaction.response.send_message("Completed")  # NOQA

    @app_commands.command(name="info", description="Show information about Member.")
    @app_commands.choices(show_private=[
        app_commands.Choice(name='No', value=0),
        app_commands.Choice(name='Yes', value=1),
    ])
    @app_commands.describe(mention="Type Member name. Example: @Hacker32Bit")
    @app_commands.describe(show_private="Type Member name. Example: @Hacker32Bit")
    async def info(self, interaction: discord.Interaction, mention: discord.Member = None,
                   show_private: app_commands.Choice[int] = 0):
        await self.show_info(interaction, mention, True if show_private and show_private.value else False)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="private_info", description="[ADMIN] Show information about Member with private fields.")
    @app_commands.describe(mention="Type Member name. Example: @Hacker32Bit")
    async def private_info(self, interaction: discord.Interaction, mention: discord.Member = None):
        await self.show_info(interaction, mention, True, True)


async def setup(bot):
    await bot.add_cog(MembersData(bot), guilds=[discord.Object(id=GUILD_ID)])
