import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os


load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")


class MemberUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Member update\" cog is ready!")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Give role when joined
        if before.pending and not after.pending:
            role = discord.utils.get(before.guild.roles, name="Member")
            await after.add_roles(role)

        # Called when member status switch from online to offline
        if before.status is discord.Status.online and after.status is discord.Status.offline:
            # print('was offline then online')
            channel = self.client.get_channel(ADMIN_LOG_CHANNEL_ID)  # admin log channel
            await channel.send(f'{after.name} is now {after.status}')

        # Change nickname alert
        if before.nick != after.nick:
            channel = await self.client.fetch_channel(LOG_CHANNEL_ID)
            if before.nick is None:
                description = (
                    f"<:pepecringe:1240238403270737951> **{after.mention}** has set nickname from default name "
                    f"**{before.name}** to **{after.nick}**!")
            elif after.nick is None:
                description = (f"<:pepecringe:1240238403270737951> **{after.mention}** has reset nickname from "
                               f"**{before.nick}** to default name **{after.name}**!")
            else:
                description = (f"<:pepecringe:1240238403270737951> **{after.mention}** has changed nickname from "
                               f"**{before.nick}** to **{after.nick}**!")
            embed = discord.Embed(
                description=description,
                color=0xcddc39,
                timestamp=datetime.datetime.now()
            )
            await channel.send(embed=embed)


async def setup(client):
    await client.add_cog(MemberUpdate(client))
