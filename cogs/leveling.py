import io
import os
import re
from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
import vacefron
import math
import sqlite3
from dotenv import load_dotenv
from PIL import Image, ImageColor

load_dotenv()
GENERAL_CHANNEL_ID: Final[str] = os.getenv("GENERAL_CHANNEL_ID")
GENERAL_VOICE_CHANNEL_ID: Final[str] = os.getenv("GENERAL_VOICE_CHANNEL_ID")
ASSETS_CHANNEL_ID: Final[str] = os.getenv("ASSETS_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS levels(user_id INTEGER, guild_id INTEGER, exp INTEGER, level INTEGER, 
                last_lvl INTEGER, background TEXT)""")


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Leveling\" cog is ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if str(message.channel.id) not in [GENERAL_CHANNEL_ID, GENERAL_VOICE_CHANNEL_ID]:
            return

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                       f"{message.author.id} and guild_id = {message.guild.id}")
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                           f"VALUES({message.author.id}, {message.guild.id}, 0, 0, 0, '')")
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

    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def sync(self, ctx) -> None:
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"synced {len(fmt)} commands")

    @app_commands.command(name="rank", description="Show user rank card.")
    async def rank(self, interaction: discord.Interaction):
        await self.show_rank(interaction)

    @commands.command(name="rank_bg", description="Set rank card background.")
    @commands.has_any_role("Owner", "Admin", "Donator")
    async def rank_bg(self, ctx, file: discord.Attachment):
        if file is None:
            print("Empty")
            return

        # fetch, send image to assets channel for store, and delete old.
        assets_channel = await self.bot.fetch_channel(ASSETS_CHANNEL_ID)
        file = await file.to_file()
        res = await assets_channel.send(f"{ctx.message.author.mention}, {ctx.message.content}\nBackground: ", file=file)
        await ctx.message.delete()

        # print(type(res), res)

        args = ctx.message.content.split(" ", 3)
        print(args)

        frame = Image.open("assets/images/ranked_card_frame.png").convert("RGBA")

        # Set color on frame if user typed color in HEX
        if len(args) > 1:
            (r, g, b) = ImageColor.getcolor(args[1], "RGB")

            pixdata = frame.load()
            for y in range(frame.size[1]):
                for x in range(frame.size[0]):
                    alpha = pixdata[x, y][3]
                    if alpha:
                        pixdata[x, y] = (r, g, b, alpha)

        # Resize and crop image to 1050x300px
        min_width, min_height = 1050, 300
        ratio = min_width / min_height
        background_image = Image.open(file.fp).convert("RGBA")

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

        width, height = background_image_sized.size
        if width > min_width:
            left = round((width - min_width) / 2)
            right = left + min_width
            top = 0
            bottom = min_height
        elif height > min_height:
            left = 0
            right = min_width
            top = round((height - min_height) / 2)
            bottom = top + min_height
        else:
            left, right, top, bottom = (0, 0, 0, 0)

        background_image_sized = background_image_sized.crop((left, top, right, bottom))

        # Add frame to background
        background_image_sized.paste(frame, (0, 0), frame)

        with io.BytesIO() as image_binary:
            background_image_sized.save(image_binary, 'PNG')
            image_binary.seek(0)
            result = discord.File(fp=image_binary, filename='rank.png')
            message = await assets_channel.send(f"Ranked card result: ", file=result)

        background_image_sized.close()
        frame.close()

        # Save image url in database
        cursor.execute(f"SELECT user_id, guild_id FROM levels WHERE user_id = "
                       f"{ctx.author.id} and guild_id = {ctx.guild.id}")
        result = cursor.fetchone()

        print(result)
        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                           f"VALUES({ctx.author.id}, {ctx.guild.id}, 0, 0, 0, '')")
            database.commit()

        cursor.execute(f"UPDATE levels SET background = '{message.attachments[0].url}' WHERE user_id = {ctx.author.id} "
                       f"AND guild_id = {ctx.guild.id}")
        database.commit()

        await assets_channel.send("Rank card image changed successfully!")

    @commands.command(name="user_rank", description="Show user rank by mention.")
    @commands.has_any_role("Owner", "Admin")
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
            await interaction.response.send_message(message) # NOQA
            return

        exp, level, last_lvl, background = result

        next_lvl_xp = ((int(level) + 1) / 0.1) ** 2
        next_lvl_xp = int(next_lvl_xp)

        rank_card = vacefron.Rankcard(
            username=user.display_name,
            avatar_url=user.avatar.url,
            current_xp=exp,
            next_level_xp=next_lvl_xp,
            previous_level_xp=0,
            level=int(level),
            rank=rank,
            circle_avatar=False,
            background=background,
            xp_color=str(user.color),
            text_shadow_color="000000",
        )

        card = await vacefron.Client().rank_card(rank_card)
        await interaction.response.send_message(card.url) # NOQA


async def setup(bot):
    await bot.add_cog(Leveling(bot), guilds=[discord.Object(id=GUILD_ID)])
