import math
import random
import sqlite3
import time
import typing

import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os
from subprocess import check_output

load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()


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
        self.client.clear()

    # Command for get server state
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def battery_status(self, ctx):
        try:
            f = open("/tmp/battery_status", "r")
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
        fmt = await ctx.bot.tree.sync(guild=discord.Object(GUILD_ID))
        await ctx.send(f"synced {len(fmt)} commands")

    # Remove referrer from DB by ID
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def remove_referrer(self, ctx: discord.ext.commands.context.Context, user_id: str) -> None:
        descending = "DELETE FROM invites WHERE user_id = ?"
        cursor.execute(descending, (user_id,))
        database.commit()

    # Remove data from activity_giveaway table
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def reset_activity_giveaway(self, ctx: discord.ext.commands.context.Context) -> None:
        descending = "DELETE FROM activity_giveaway"
        cursor.execute(descending)
        database.commit()

    # Add exp to user_id
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def add_exp(self, ctx: discord.ext.commands.context.Context, user_id: str, add_exp: str) -> None:
        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                       f"{user_id} and guild_id = {ctx.guild.id}")
        activity_giveaway_result = cursor.fetchone()

        if activity_giveaway_result is None:
            cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                           f"VALUES({user_id}, {ctx.guild.id}, {int(add_exp)}, 0, 0)")
            database.commit()
        else:
            user_id, guild_id, exp, level, last_lvl = activity_giveaway_result

            # Give 150 XP for invite
            exp_gained = int(add_exp)
            exp += exp_gained
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(
                f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                f"guild_id = {guild_id}")
            database.commit()

    # Reduce exp to user_id
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def reduce_exp(self, ctx: discord.ext.commands.context.Context, user_id: str, reduce_exp: str) -> None:
        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                       f"{user_id} and guild_id = {ctx.guild.id}")
        activity_giveaway_result = cursor.fetchone()

        if activity_giveaway_result is None:
            cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                           f"VALUES({user_id}, {ctx.guild.id}, 0, 0, 0)")
            database.commit()
        else:
            user_id, guild_id, exp, level, last_lvl = activity_giveaway_result

            # Give 150 XP for invite
            exp_gained = int(reduce_exp)
            exp -= exp_gained
            if exp < 0:
                exp = 0
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(
                f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                f"guild_id = {guild_id}")
            database.commit()

    # Command for send message from Bot
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def send_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message: str) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("message: ", message)
        await channel.send(content=message)

    # Command for send file from Bot
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def send_file(self, ctx: discord.ext.commands.context.Context, channel_id: str,
                        file: discord.Attachment) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("file: ", file)
        await channel.send(file=await file.to_file())

    # Command for send message with file from Bot
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def send_embed_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message: str,
                                 file: discord.Attachment) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("message: ", message)
        print("file: ", file)
        await channel.send(content=message, file=await file.to_file())

    # Command for send message with file from Bot
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def edit_file(self, ctx: discord.ext.commands.context.Context, channel_id: str, message_id: str,
                           file: discord.Attachment) -> None:
        print("channel_id: ", channel_id)
        print("message_id: ", message_id)
        print("file: ", file)

        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        await message.edit(attachments=[file])

    # Command for send message with file from Bot
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def edit_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message_id: str,
                                 message_text: str) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("message_id: ", message_id)
        print("message_text: ", message_text)

        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        await message.edit(content=message_text)

    # Command for send message with file from Bot
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def edit_embed_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message_id: str,
                                 message_text: str, files: typing.Union[discord.Attachment]) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("message_id: ", message_id)
        print("message_text: ", message_text)
        print("type file: ", type(files))
        print("file: ", files)

        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        await message.edit(content=message_text, attachments=[files])

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
            description=f":tada: Congrats{winners[:len(winners) - 1]}!\nYou are very lucky in this giveaway!",
            color=0x9C27B0,
            timestamp=datetime.datetime.now()
        )
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(AdminCommands(client))
