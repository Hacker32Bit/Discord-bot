import os
import re
from typing import Final
import discord
from discord import app_commands
from discord.ext import commands
import vacefron
import math
import random
import sqlite3
from dotenv import load_dotenv

load_dotenv()
SPAM_CHANNEL_ID: Final[str] = os.getenv("SPAM_CHANNEL_ID")
ADMIN_SPAM_CHANNEL_ID: Final[str] = os.getenv("ADMIN_SPAM_CHANNEL_ID")
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

        if str(message.channel.id) in [SPAM_CHANNEL_ID, ADMIN_SPAM_CHANNEL_ID]:
            return

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                       f"{message.author.id} and guild_id = {message.guild.id}")
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                           f"VALUES({message.author.id}, {message.guild.id}, 0, 0, 0, "")")
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
                    role = discord.utils.get(message.guild.roles, name="Advanced (15 LVL)")
                    await user.add_roles(role)
                elif int(level) == 25:
                    role = discord.utils.get(message.guild.roles, name="Advanced (15 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Expert (25 LVL)")
                    await user.add_roles(role)
                elif int(level) == 50:
                    role = discord.utils.get(message.guild.roles, name="Expert (25 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Elite (50 LVL)")
                    await user.add_roles(role)
                elif int(level) == 100:
                    role = discord.utils.get(message.guild.roles, name="Elite (50 LVL)")
                    await user.remove_roles(role)
                    role = discord.utils.get(message.guild.roles, name="Godly (100 LVL)")
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

    @commands.command(name="user_rank", description="Show user rank by mention")
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
