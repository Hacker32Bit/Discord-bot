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
HACKER_BOT_ID: Final[str] = os.getenv("HACKER_BOT_ID")
HACKER_ID: Final[str] = os.getenv("HACKER_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS activity_giveaway(user_id INTEGER NOT NULL, guild_id INTEGER NOT NULL, 
exp INTEGER, level INTEGER, last_lvl INTEGER, PRIMARY KEY("user_id"));""")


class ActivityGiveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = dict()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Activity Giveaway\" cog is ready!")
        await self.initialize_active_voice_members()

    def cog_unload(self):
        for member_id in self.data:
            cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                           f"{member_id} and guild_id = {GUILD_ID}")
            result = cursor.fetchone()

            # print(result)

            if result is None:
                cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                               f"VALUES({member_id}, {GUILD_ID}, 0, 0, 0)")
                database.commit()

            minutes_per_point = (time.time() - self.data[member_id]) // 600

            user_id, guild_id, exp, level, last_lvl = result

            # print(minutes_per_point)

            exp_gained = minutes_per_point + 1
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()

            del self.data[user_id]

        print("[INFO] Cog \"Activity Giveaway\" was unloaded!")

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
                if member.bot or str(member.id) in [HACKER_ID, HACKER_BOT_ID]:
                    continue

                self.data[member.id] = time.time()
                print(f"[INIT] Tracking member {member.display_name} in voice channel {voice_channel.name}")

    # Message listener for give 1-20XP
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or str(message.author.id) in [HACKER_ID]:
            return

        if str(message.channel.id) not in [GENERAL_TEXT_CHANNEL_ID, GENERAL_VOICE_CHANNEL_ID]:
            return

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                       f"{message.author.id} and guild_id = {message.guild.id}")
        result = cursor.fetchone()

        if result is None:
            cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                           f"VALUES({message.author.id}, {message.guild.id}, 0, 0, 0)")
            database.commit()
        else:
            user_id, guild_id, exp, level, last_lvl = result

            exp_gained = await self.calculate_xp(message=str(message.content))

            exp_gained = math.floor(exp_gained)
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()

        await self.bot.process_commands(message)

    # Listener for give 1XP every 10 minutes
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if str(member.id) in [HACKER_ID, HACKER_BOT_ID]:
            return
        if after.channel and after.channel.id in [STREAMS_VOICE_CHANNEL_ID, MUSIC_VOICE_CHANNEL_ID,
                                                  AFK_VOICE_CHANNEL_ID]:
            # print("inside first if")
            return

        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                       f"{member.id} and guild_id = {member.guild.id}")
        result = cursor.fetchone()

        # print(result)

        if result is None:
            cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                           f"VALUES({member.id}, {member.guild.id}, 0, 0, 0)")
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

            cursor.execute(f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                           f"guild_id = {guild_id}")
            database.commit()
            del self.data[member.id]

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


async def setup(bot):
    await bot.add_cog(ActivityGiveaway(bot), guilds=[discord.Object(id=GUILD_ID)])
