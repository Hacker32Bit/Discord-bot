from discord.ext import commands
from dotenv import load_dotenv
from typing import Final
import os


load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")


class BanAndMute(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Welcome & Goodbye\" cog is ready!")

    @commands.Cog.listener()
    async def on_member_ban(self):

        print("test")


async def setup(client):
    await client.add_cog(BanAndMute(client))
