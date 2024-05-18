import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os


load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")


class AdminCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Admin commands\" cog is ready!")

    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def join_user(self, member_id, user_id) -> None:
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            description=f":wave: Welcome to server **<@{user_id}>**!",
            color=0x4caf50,
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)


async def setup(client):
    await client.add_cog(AdminCommands(client))
