import io
import os
import re
import time
from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
from disrank.generator import Generator
import math
import sqlite3
from dotenv import load_dotenv
from PIL import Image, ImageColor

load_dotenv()
GENERAL_TEXT_CHANNEL_ID: Final[str] = os.getenv("GENERAL_TEXT_CHANNEL_ID")
GENERAL_VOICE_CHANNEL_ID: Final[str] = os.getenv("GENERAL_VOICE_CHANNEL_ID")
STREAMS_VOICE_CHANNEL_ID: Final[str] = os.getenv("STREAMS_VOICE_CHANNEL_ID")
MUSIC_VOICE_CHANNEL_ID: Final[str] = os.getenv("MUSIC_VOICE_CHANNEL_ID")
AFK_VOICE_CHANNEL_ID: Final[str] = os.getenv("AFK_VOICE_CHANNEL_ID")
ASSETS_CHANNEL_ID: Final[str] = os.getenv("ASSETS_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS levels(user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, exp INTEGER, 
level INTEGER, last_lvl INTEGER, background INTEGER, PRIMARY KEY("user_id"));""")


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = dict()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Leveling\" cog is ready!")
        await self.initialize_active_voice_members()

    def cog_unload(self):
        for member_id in self.data:
            cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                           f"{member_id} and guild_id = {GUILD_ID}")
            result = cursor.fetchone()

            # print(result)

            if result is None:
                cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl) "
                               f"VALUES({member_id}, {GUILD_ID}, 0, 0, 0)")
                database.commit()

            minutes_per_point = (time.time() - self.data[member_id]) // 600

            user_id, guild_id, exp, level, last_lvl = result

            # print(minutes_per_point)

            exp_gained = minutes_per_point + 1
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE levels SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()

            del self.data[user_id]

        print("[INFO] Cog \"Leveling\" was unloaded!")

    async def initialize_active_voice_members(self):
        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(int(GUILD_ID))
        if not guild:
            print(f"[ERROR] Guild with ID {GUILD_ID} not found")
            return

        for voice_channel in guild.voice_channels:
            # Skip excluded channels
            if str(voice_channel.id) in [STREAMS_VOICE_CHANNEL_ID, MUSIC_VOICE_CHANNEL_ID, AFK_VOICE_CHANNEL_ID]:
                continue

            for member in voice_channel.members:
                self.data[member.id] = time.time()
                print(f"[INIT] Tracking member {member.display_name} in voice channel {voice_channel.name}")

    # Message listener for give 1-20XP
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if str(message.channel.id) not in [GENERAL_TEXT_CHANNEL_ID, GENERAL_VOICE_CHANNEL_ID]:
            return

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                       f"{message.author.id} and guild_id = {message.guild.id}")
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                           f"VALUES({message.author.id}, {message.guild.id}, 0, 0, 0, 0)")
            database.commit()
        else:
            user_id, guild_id, exp, level, last_lvl = result

            exp_gained = await self.calculate_xp(message=str(message.content))

            exp_gained = math.floor(exp_gained)
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE levels SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()

            if int(level) > last_lvl:
                cursor.execute(f"UPDATE levels SET last_lvl = {int(level)} WHERE user_id = {user_id} AND "
                               f"guild_id = {guild_id}")
                database.commit()

                user = message.author

                if int(level) == 5:
                    role = discord.utils.get(message.guild.roles, name="Beginner (5 LVL)")
                    await user.add_roles(role)
                elif int(level) == 10:
                    role = discord.utils.get(message.guild.roles, name="Beginner (5 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Intermediate (10 LVL)")
                    await user.add_roles(role)
                elif int(level) == 15:
                    role = discord.utils.get(message.guild.roles, name="Intermediate (10 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Advanced (20 LVL)")
                    await user.add_roles(role)
                elif int(level) == 25:
                    role = discord.utils.get(message.guild.roles, name="Advanced (20 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Expert (30 LVL)")
                    await user.add_roles(role)
                elif int(level) == 50:
                    role = discord.utils.get(message.guild.roles, name="Expert (30 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Elite (40 LVL)")
                    await user.add_roles(role)
                elif int(level) == 100:
                    role = discord.utils.get(message.guild.roles, name="Elite (40 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Godly (50 LVL)")
                    await user.add_roles(role)

                await message.channel.send(f"{message.author.mention} has leveled up to level {int(level)}!")

        await self.bot.process_commands(message)

    # Listener for give 1XP every 10 minutes
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.id in [STREAMS_VOICE_CHANNEL_ID, MUSIC_VOICE_CHANNEL_ID,
                                                  AFK_VOICE_CHANNEL_ID]:
            # print("inside first if")
            return

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                       f"{member.id} and guild_id = {member.guild.id}")
        result = cursor.fetchone()

        # print(result)

        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                           f"VALUES({member.id}, {member.guild.id}, 0, 0, 0, 0)")
            database.commit()

        if not before.channel and after.channel:
            self.data[member.id] = time.time()

        elif before.channel and not after.channel and member.id in self.data:
            minutes_per_point = (time.time() - self.data[member.id]) // 600

            user_id, guild_id, exp, level, last_lvl = result

            # print(minutes_per_point)

            exp_gained = minutes_per_point
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE levels SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()

            del self.data[member.id]

            if int(level) > last_lvl:
                cursor.execute(f"UPDATE levels SET last_lvl = {int(level)} WHERE user_id = {user_id} AND "
                               f"guild_id = {guild_id}")
                database.commit()

                if int(level) == 5:
                    role = discord.utils.get(member.guild.roles, name="Beginner (5 LVL)")
                    await member.add_roles(role)
                elif int(level) == 10:
                    role = discord.utils.get(member.guild.roles, name="Beginner (5 LVL)")
                    await member.remove_roles(role)
                    role = discord.utils.get(member.guild.roles, name="Intermediate (10 LVL)")
                    await member.add_roles(role)
                elif int(level) == 15:
                    role = discord.utils.get(member.guild.roles, name="Intermediate (10 LVL)")
                    await member.remove_roles(role)
                    role = discord.utils.get(member.guild.roles, name="Advanced (20 LVL)")
                    await member.add_roles(role)
                elif int(level) == 25:
                    role = discord.utils.get(member.guild.roles, name="Advanced (20 LVL)")
                    await member.remove_roles(role)
                    role = discord.utils.get(member.guild.roles, name="Expert (30 LVL)")
                    await member.add_roles(role)
                elif int(level) == 50:
                    role = discord.utils.get(member.guild.roles, name="Expert (30 LVL)")
                    await member.remove_roles(role)
                    role = discord.utils.get(member.guild.roles, name="Elite (40 LVL)")
                    await member.add_roles(role)
                elif int(level) == 100:
                    role = discord.utils.get(member.guild.roles, name="Elite (40 LVL)")
                    await member.remove_roles(role)
                    role = discord.utils.get(member.guild.roles, name="Godly (50 LVL)")
                    await member.add_roles(role)

                await after.channel.send(f"{member.mention} has leveled up to level {int(level)}!")

    # Method for calculate XP on message
    @staticmethod
    async def calculate_xp(message: str):
        url_pattern = re.compile(r'https?://\S+|www\.\S+')

        # Use the sub() method to replace URLs with the specified replacement text
        text_without_urls = url_pattern.sub("", message)

        text_length = len(text_without_urls)

        t = 20
        b = 200

        if text_length >= b:
            return t

        k = 0.5
        d = 0.5
        f_x = math.log(text_length / b + 1, 10)
        f_x_1 = math.log(2 - text_length / b, 10)
        res = (f_x ** d) / (f_x ** d + f_x_1 ** k)

        return t * res

    @app_commands.command(name="rank", description="Show user rank card.")
    async def rank(self, interaction: discord.Interaction):
        await self.show_rank(interaction)

    @app_commands.command(name="rank_card_setting", description="Set rank card background.")
    @app_commands.choices(reset=[
        app_commands.Choice(name='Yes', value=1),
        app_commands.Choice(name='No', value=0)
    ])
    @app_commands.describe(image="Select image if you want change rank card background. [.jpg, .jpeg, .png, .bmp, "
                                 ".gif, .webp, .tif]")
    @app_commands.describe(color="Enter color code in HEX. Example: `fff`, `#fff`, `123abc`, or `#a1b2f9`.")
    @app_commands.describe(reset="Select `Yes` if you want reset your rank card design!")
    async def rank_card_setting(self, interaction: discord.Interaction, image: discord.Attachment = None,
                                color: str = None, reset: app_commands.Choice[int] = 0):
        # Make timelimit more than 3 sec for slash commands
        await interaction.response.defer()  # NOQA

        if image is None and color is None and reset == 0:
            await interaction.followup.send(f"Please, provide at least one argument.")
            return

        if color:
            color = color.lstrip()
            if color[0] != "#":
                color = f"#{color}"

            if not (len(color) == 4 or len(color) == 7):
                await interaction.followup.send(f"Wrong `color: ` argument length!")
                return
            else:
                for i in range(1, len(color)):
                    if (not (('0' <= color[i] <= '9') or ('a' <= color[i] <= 'f') or (
                            color[i] >= 'A' or color[i] <= 'F'))):
                        await interaction.followup.send(f"Wrong `color: ` argument values!")
                        return

        # Get data from db.
        cursor.execute(f"SELECT user_id, guild_id FROM levels WHERE user_id = "
                       f"{interaction.user.id} and guild_id = {interaction.guild.id}")
        result = cursor.fetchone()

        # if data not exist add empty values
        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                           f"VALUES({interaction.user.id}, {interaction.guild.id}, 0, 0, 0, 0)")
            database.commit()

        # If user need reset card to default
        if reset and reset.value:
            # print("Reset: True")
            cursor.execute(
                f"UPDATE levels SET background = 0 WHERE user_id = {interaction.user.id} "
                f"AND guild_id = {interaction.guild.id}")
            database.commit()
            await interaction.followup.send(f"You have reset your rank card to default!")
            return

        if image is not None:
            # print(image.content_type.split("/")[1])
            if image.content_type.split("/")[1] not in ["png", "jpg", "jpeg", "bmp", "gif", "tiff", "webp"]:
                await interaction.followup.send("Not allowed! Please, use only images.")
                return

            # fetch, send image to assets channel for store.
            assets_channel = await self.bot.fetch_channel(ASSETS_CHANNEL_ID)
            image = await image.to_file()
            await assets_channel.send(f"User: {interaction.user.mention}, Color: {color}, Reset: {reset}\n"
                                      f"Background: ", file=image)

            with Image.open("assets/images/ranked_card_frame.png") as frame:
                # Set color on frame if user typed color in HEX
                if color:
                    (r, g, b) = ImageColor.getcolor(color, "RGB")

                    pix_data = frame.load()
                    for y in range(frame.size[1]):
                        for x in range(frame.size[0]):
                            alpha = pix_data[x, y][3]
                            if alpha:
                                pix_data[x, y] = (r, g, b, alpha)

                # Resize and crop image to 900x238px
                min_width, min_height = 900, 238
                ratio = min_width / min_height

                with Image.open(image.fp) as background_image:
                    width, height = background_image.size

                    # check ratio difference for resize by width or height
                    # By width
                    if width / height >= ratio:
                        new_height = min_height
                        new_width = round(new_height * width / height)
                        # By height
                    else:
                        new_width = min_width
                        new_height = round(new_width * height / width)

                    background_image_sized = background_image.resize((new_width, new_height))

                    # Ensure new image fully covers the target box
                    new_width, new_height = background_image_sized.size

                    left = max(0, (new_width - min_width) // 2)
                    top = max(0, (new_height - min_height) // 2)

                    right = min(new_width, left + min_width)
                    bottom = min(new_height, top + min_height)

                    background_image_sized = background_image_sized.crop((left, top, right, bottom))

                    # Add frame to background
                    background_image_sized.paste(frame, (0, 0), frame.convert('RGBA'))

                    with io.BytesIO() as image_binary:
                        background_image_sized.save(image_binary, format="PNG")
                        background_image_sized.save(f"assets/images/rank_cards/{interaction.user.id}.png", format="PNG")
                        image_binary.seek(0)
                        result = discord.File(fp=image_binary, filename="rank_card.png")
                        await assets_channel.send(f"Ranked card result: ", file=result)

        elif color:
            # fetch, send frame to assets channel for store.
            assets_channel = await self.bot.fetch_channel(ASSETS_CHANNEL_ID)

            with Image.open("assets/images/ranked_card_frame.png") as frame:
                with Image.open("assets/images/blank_rank_card.png") as background_image_sized:
                    (r, g, b) = ImageColor.getcolor(color, "RGB")

                    pix_data = frame.load()
                    for y in range(frame.size[1]):
                        for x in range(frame.size[0]):
                            alpha = pix_data[x, y][3]
                            if alpha:
                                pix_data[x, y] = (r, g, b, alpha)

                    background_image_sized.paste(frame, (0, 0), frame.convert('RGBA'))

                    with io.BytesIO() as image_binary:
                        background_image_sized.save(image_binary, 'PNG')
                        background_image_sized.save(f"assets/images/rank_cards/{interaction.user.id}.png", format="PNG")
                        image_binary.seek(0)
                        result = discord.File(fp=image_binary, filename='rank.png')
                        await assets_channel.send(f"Ranked card result: ", file=result)

        cursor.execute(f"UPDATE levels SET background = 1 WHERE user_id = "
                       f"{interaction.user.id} AND guild_id = {interaction.guild.id}")
        database.commit()

        await interaction.followup.send(f"You have updated your rank card design!")

    @app_commands.command(name="user_rank", description="Show user rank by mention.")
    async def user_rank(self, interaction: discord.Interaction, user: discord.Member):
        await self.show_rank(interaction, user)

    @staticmethod
    async def show_rank(interaction: discord.Interaction, user: discord.Member = None) -> None:
        if user is None:
            user = interaction.user

        rank = 1

        descending = "SELECT * FROM levels WHERE guild_id = ? ORDER BY exp DESC"
        cursor.execute(descending, (interaction.guild.id,))
        result = cursor.fetchall()

        for i in range(len(result)):
            if result[i][0] == user.id:
                break
            else:
                rank += 1

        cursor.execute(f"SELECT exp, level, last_lvl, background FROM levels WHERE user_id = {user.id} AND "
                       f"guild_id = {interaction.guild.id}")
        result = cursor.fetchone()

        if result is None:
            message = ("You dont have any XP, because you dont have activity.\nPlease type some messages in "
                       "\"〔💬〕general \" channel or join in voice channel at least 10 minutes.")
            await interaction.response.send_message(message)  # NOQA
            return

        exp, level, last_lvl, background = result

        next_lvl_xp = ((int(level) + 1) / 0.1) ** 2
        next_lvl_xp = int(next_lvl_xp)

        user_status = interaction.guild.get_member(user.id).status

        background_link = os.path.join(os.path.dirname(__file__), os.path.pardir, 'assets', 'images', 'rank_cards',
                                       f'{interaction.user.id}.png')
        # try:
        #     user_picture = user.avatar.url
        # except AttributeError:
        #     user_picture = f'https://cdn.discordapp.com/embed/avatars/{random.randrange(5)}.png'

        args = {
            'bg_image': background_link if int(background) else None,  # Background image link
            'profile_image': user.display_avatar.url,  # User profile picture link
            'level': int(level),  # User current level
            'current_xp': int(level) ** 2 * 100,  # Current level minimum xp
            'user_xp': exp,  # User current xp
            'next_xp': next_lvl_xp,  # xp required for next level
            'user_position': rank,  # User position in leaderboard
            'user_name': user.display_name,  # username with descriminator
            'user_status': user_status.__str__(),  # User status eg. online, offline, idle, streaming, dnd
            'xp_color': user.color.__str__(),
        }

        image = Generator().generate_profile(**args)
        file = discord.File(fp=image, filename='image.png')

        await interaction.response.send_message(file=file)  # NOQA


async def setup(bot):
    await bot.add_cog(Leveling(bot), guilds=[discord.Object(id=GUILD_ID)])
