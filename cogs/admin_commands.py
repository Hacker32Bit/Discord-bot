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
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")


class AdminCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Admin commands\" cog is ready!")

    # Command for shutdown bot (restart bot)
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def shutdown(self, ctx):
        print("[INFO] logging out...")
        await self.client.close()

    # Command for get server state
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def battery_status(self, ctx):
        try:
            f = open("/tmp/battery_status.txt", "r")
            await ctx.send(f.read())
        except FileNotFoundError as e:
            await ctx.send(e)

    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def temp_status(self, ctx):
        try:
            result = check_output(["/usr/bin/bash", "scripts/my_pi_temp.sh"]).strip().decode("utf-8")
            await ctx.send(result)
        except Exception as e:
            await ctx.send(e)

    # Command for synchronize client slash commands with server commands
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def sync(self, ctx) -> None:
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"synced {len(fmt)} commands")

    # Command for add manually join user log in log channel
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

    # Command for get members dict() who reacted on post by message_id
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def get_members_list(self, ctx, message_id):
        await ctx.message.delete()
        channel = self.client.get_channel(ctx.channel.id)
        message = await channel.fetch_message(message_id)
        users = set()
        for reaction in message.reactions:
            async for user in reaction.users():
                users.add(user)
        await ctx.send(f"Users: {', '.join(user.mention for user in users)}")
        return users

    # Command for get random winner from message reactions
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def giveaway_random(self, ctx, message_id, count, repeat: str = None) -> None:
        await ctx.send(f"Participants of the competition.")
        get_all_reacted_users = await self.get_members_list(ctx, message_id)

        winners = " "
        for i in range(int(count)):
            print("inside for ", i)
            time.sleep(random.randint(500, 1500) / 1000)
            winner = random.choice(list(get_all_reacted_users))

            if repeat is None:
                get_all_reacted_users.remove(winner)

            winners += f"{winner.mention},"

        embed = discord.Embed(
            description=f":tada: Congrats{winners[:len(winners)-1]}!\nYou are very lucky in this giveaway!",
            color=0x9C27B0,
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(AdminCommands(client))
