import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os


load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")


class WelcomeAndGoodbye(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Welcome & Goodbye\" cog is ready!")

    @commands.Cog.listener()
    async def on_member_join(self, member) -> None:
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            description=f":wave: Welcome to server **{member.mention}**!",
            color=0x4caf50,
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member) -> None:
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            description=f"<:hmm2:1240238779181174825> **{member.mention}** leaved from this server!",
            color=0xff9800,
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)


async def setup(client):
    await client.add_cog(WelcomeAndGoodbye(client))
