import discord
from discord.ext import commands
import vacefron
import math
import random
import sqlite3

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS levels(user_id INTEGER, guild_id INTEGER, exp INTEGER, level INTEGER, 
                last_lvl INTEGER)""")


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

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                       f"{message.author.id} and guild_id = {message.guild.id}")
        result = cursor.fetchone()
        if result is None:
            cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl) VALUES({message.author.id}, "
                           f"{message.guild.id}, 0, 0, 0)")
            database.commit()
        else:
            user_id, guild_id, exp, level, last_lvl = result

            exp_gained = random.randint(1, 20)
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE levels SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()
            if int(level) > last_lvl:
                await message.channel.send(f"{message.author.mention} has leveled up to level {int(lvl)}!")
                cursor.execute(f"UPDATE levels SET last_lvl = {int(level)} WHERE user_id = {user_id} AND "
                               f"guild_id = {guild_id}")
                database.commit()

    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def rank(self, interaction):
        rank = 1

        descending = "SELECT * FROM levels WHERE guild_id = ? ORDER BY exp DESC"
        cursor.execute(descending, (interaction.guild.id,))
        result = cursor.fetchall()

        for i in range(len(result)):
            if result[i][0] == interaction.author.id:
                break
            else:
                rank += 1

        cursor.execute(f"SELECT exp, level, last_lvl FROM levels WHERE user_id = {interaction.author.id} AND "
                       f"guild_id = {interaction.guild.id}")
        result = cursor.fetchone()

        exp, level, last_lvl = result

        next_lvl_xp = ((int(level) + 1) / 0.1) ** 2
        next_lvl_xp = int(next_lvl_xp)

        rank_card = vacefron.Rankcard(
            username=interaction.author.display_name,
            avatar_url=interaction.author.avatar.url,
            current_xp=exp,
            next_level_xp=next_lvl_xp,
            previous_level_xp=0,
            level=int(level),
            rank=rank
        )

        card = await vacefron.Client().rank_card(rank_card)
        await interaction.send(card.url)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
