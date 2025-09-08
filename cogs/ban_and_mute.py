import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from typing import Final
import datetime
import os
import sqlite3
import re
import math

load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")
RULES_TEXT_CHANNEL_ID: Final[str] = os.getenv("RULES_TEXT_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

rules = {
    1: 1237305224075542548,
    2: 1237305310956359710,
    3: 1237305788817473547,
    4: 1237305879448260608,
    5: 1237306073988333608,
    6: 1237306115709075486,
}

class BanAndMute(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.conn = sqlite3.connect("database.sqlite")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS temp_bans (
                        user_id INTEGER,
                        guild_id INTEGER,
                        end_time INTEGER,
                        reason TEXT,
                        PRIMARY KEY (user_id, guild_id)
                    )
                """)
        self.conn.commit()
        self.check_bans.start()  # start background task

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Ban & Mute\" cog is ready!")

    def cog_unload(self):
        self.check_bans.cancel()
        self.conn.close()
        print("[INFO] Cog \"Ban & Mute\" was unloaded!")

    @staticmethod
    def string_to_array(s: str) -> list[float]:
        # Find all valid float-like numbers using regex
        numbers = re.findall(r"-?\d+(?:\.\d+)?", s)
        return [float(num) for num in numbers] if numbers else []

    async def get_specific_message(self, message_id: int):
        channel = await self.client.fetch_channel(RULES_TEXT_CHANNEL_ID)  # Get the channel object
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                return message.content
            except discord.NotFound:
                return "Message not found in that channel."
            except discord.Forbidden:
                return "I don't have permission to access that channel."
        else:
            return "Channel not found."

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, length: int = 0, *, reason: str = "No reason provided"):
        """
        Ban a member. If length > 0, the ban is temporary (in days).
        Example: !ban @user 14 Spamming
        """
        channel = await self.client.fetch_channel(1241019624313851969)
        reasons = self.string_to_array(reason)

        pm_message = "I'm sorry... You have banned for:\n"
        reason_messages = reason
        if len(reasons) > 0:
            pm_message += "```"
            reason_messages = ""
            for r in reasons:
                print(r)
                message_id = rules[math.floor(r)]
                print(message_id)
                text = await self.get_specific_message(message_id)
                print(text)
                pm_message += str(r) + text.split(str(r))[1].split('\n')[0] + "\n"
                reason_messages += f"[{r}](https://discord.com/channels/{GUILD_ID}/{RULES_TEXT_CHANNEL_ID}/{message_id}), "
            pm_message += "```"
            reason_messages = reason_messages[:-2]

        await self.client.send_message(member, pm_message)
        await member.ban(reason=reason)
        end_time = None

        if length > 0:
            end_time = int((datetime.datetime.utcnow() + datetime.timedelta(days=length)).timestamp())
            self.cursor.execute(
                "INSERT OR REPLACE INTO temp_bans (user_id, guild_id, end_time, reason) VALUES (?, ?, ?, ?)",
                (member.id, ctx.guild.id, end_time, reason),
            )
            self.conn.commit()

        embed = discord.Embed(
            description=f"<:utilitybanhammer:1240238885762633799> **{member.mention}** was banned!\n"
                        f"**Reason**: {reason_messages}\n"
                        f"**Duration**: {'Permanent' if length == 0 else f'{length} days'}",
            color=0xB71C1C, #RED 900
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason="No reason provided"):
        channel = await self.client.fetch_channel(1241019624313851969)

        await ctx.guild.unban(user, reason=reason)
        self.cursor.execute("DELETE FROM temp_bans WHERE user_id = ? AND guild_id = ?", (user.id, ctx.guild.id))
        self.conn.commit()

        embed = discord.Embed(
            description=f"<:utilitybanhammer:1240238885762633799> **{user.mention}** was unbanned!\n**Reason**: {reason}",
            color=0x1B5E20, #GREEN 900
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)

    @tasks.loop(hours=1)
    async def check_bans(self):
        """Check every 1 hour if a temporary ban expired."""
        now = int(datetime.datetime.utcnow().timestamp())
        self.cursor.execute("SELECT user_id, guild_id, reason FROM temp_bans WHERE end_time <= ?", (now,))
        expired_bans = self.cursor.fetchall()

        for user_id, guild_id, reason in expired_bans:
            guild = self.client.get_guild(guild_id)
            if guild:
                user = discord.Object(id=user_id)
                try:
                    await guild.unban(user, reason="Temporary ban expired")
                    channel = await self.client.fetch_channel(1241019624313851969)
                    embed = discord.Embed(
                        description=f"<:utilitybanhammer:1240238885762633799> **<@{user_id}>** was automatically unbanned (ban expired)",
                        color=0x1B5E20, #GREEN 900
                        timestamp=datetime.datetime.now()
                    )
                    await channel.send(embed=embed)
                except Exception as e:
                    print(f"[ERROR] Could not unban {user_id} in guild {guild_id}: {e}")

            # Remove from DB
            self.cursor.execute("DELETE FROM temp_bans WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            self.conn.commit()

    @check_bans.before_loop
    async def before_check_bans(self):
        await self.client.wait_until_ready()


async def setup(client):
    await client.add_cog(BanAndMute(client))
