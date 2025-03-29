import math
import random
import time

import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os
from subprocess import check_output

load_dotenv()
EVENTS_CHANNEL_ID: Final[str] = os.getenv("EVENTS_CHANNEL_ID")


class CaseOpening(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Case opening\" cog is ready!")

    # Command for open case event
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def open_cs_case(self, ctx: discord.ext.commands.context.Context, user_id: str, case_name: str, quality: str, drop_name: str,
                                 file: discord.Attachment) -> None:
        channel = await self.client.fetch_channel(EVENTS_CHANNEL_ID)
        print("user_id: ", user_id)
        print("case_name: ", case_name)
        print("quality: ", quality)
        print("drop_name: ", drop_name)
        print("file: ", file)
        result = "" + user_id + case_name + drop_name + quality
        await channel.send(content=result, file=await file.to_file())


async def setup(client):
    await client.add_cog(CaseOpening(client))
