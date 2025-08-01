import math
import random
import sqlite3
import time
import sys
import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os
from subprocess import check_output
import asyncio

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
        print("[INFO] \"Admin Commands\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Admin Commands\" was unloaded!")

    async def perform_shutdown(self, code):
        await self.client.close()
        sys.exit(code)

    # Command for logout bot (logout bot)
    @commands.command(help="logout", description="Command for logout bot (logout bot)")
    @commands.has_any_role("Owner", "Admin")
    async def logout(self, ctx):
        print("[INFO] logging out...")
        await ctx.send("Goodbye. You can wake me up from Raspberry PI(Or wait for auto reboot)")

        # Shutdown outside of task loop to avoid hanging
        loop = asyncio.get_running_loop()
        loop.call_soon(asyncio.create_task, self.perform_shutdown(0))

    # Command for shutdown system
    @commands.command(help="shutdown", description="Command for shutdown system")
    @commands.has_any_role("Owner", "Admin")
    async def shutdown(self, ctx):
        print("[INFO] Shutting down...")
        try:
            # Write intent for backup script
            with open("/tmp/bot_action", "w") as f:
                f.write("shutdown")

            await ctx.send("Shutdown initiated. Backing up and turning off...")
            # Shutdown outside of task loop to avoid hanging
            loop = asyncio.get_running_loop()
            loop.call_soon(asyncio.create_task, self.perform_shutdown(0))
        except Exception as e:
            await ctx.send(e)

    # Command for reboot system (reboot Raspberry PI)
    @commands.command(help="reboot", description="Command for reboot system (reboot Raspberry PI)")
    @commands.has_any_role("Owner", "Admin")
    async def reboot(self, ctx):
        print("[INFO] Rebooting...")
        try:
            # Write intent for backup script
            with open("/tmp/bot_action", "w") as f:
                f.write("reboot")

            await ctx.send("Reboot initiated. Backing up and restarting...")
            # Shutdown outside of task loop to avoid hanging
            loop = asyncio.get_running_loop()
            loop.call_soon(asyncio.create_task, self.perform_shutdown(0))
        except Exception as e:
            await ctx.send(e)

    # Command for update system
    @commands.command(help="update", description="Command for update system")
    @commands.has_any_role("Owner", "Admin")
    async def update(self, ctx):
        print("[INFO] Updating project...")
        try:
            result = check_output(["git", "pull"]).strip().decode("utf-8")
            await ctx.send(f"```{result}```")
        except Exception as e:
            await ctx.send(e)

    # Command for update and restart bot
    @commands.command(help="restart", description="Command for update and restart bot")
    @commands.has_any_role("Owner", "Admin")
    async def restart(self, ctx):
        await self.update(ctx)

        await ctx.send("```Shutting down cleanly...```")
        try:
            # Shutdown outside of task loop to avoid hanging
            loop = asyncio.get_running_loop()
            loop.call_soon(asyncio.create_task, self.perform_shutdown(1)) # Error code for Restart=on-failure
        except Exception as e:
            await ctx.send(e)

    # Command for get server battery status
    @commands.command(help="battery_status", description="Command for get server battery status")
    @commands.has_any_role("Owner", "Admin")
    async def battery_status(self, ctx):
        try:
            f = open("/tmp/battery_status", "r")
            await ctx.send(f"```{f.read()}```")
        except FileNotFoundError as e:
            await ctx.send(e)

    # Command for get server temperature status
    @commands.command(help="temp_status", description="Command for get server temperature status")
    @commands.has_any_role("Owner", "Admin")
    async def temp_status(self, ctx):
        try:
            result = "```"
            result += check_output(["/usr/bin/bash", "scripts/my_pi_temp.sh"]).strip().decode("utf-8")
            result += "```"
            await ctx.send(result)
        except Exception as e:
            await ctx.send(e)

    # Command for get server connection status
    @commands.command(help="connection_status", description="Command for get server connection status")
    @commands.has_any_role("Owner", "Admin")
    async def connection_status(self, ctx):
        try:
            result = "```"
            scan = check_output(["/bin/nmcli", "device", "wifi", "rescan"]).strip().decode("utf-8")
            result += check_output(["/bin/nmcli", "device", "wifi", "list"]).strip().decode("utf-8")
            result += "\n" + 89 * "-" + "\n"
            result += check_output(["/bin/nmcli", "connection", "show"]).strip().decode("utf-8")
            result += "```"
            await ctx.send(result)
        except Exception as e:
            await ctx.send(e)

    # Command for synchronize client slash commands with server commands
    @commands.command(help="sync", description="Command for synchronize client slash commands with server commands")
    @commands.has_any_role("Owner", "Admin")
    async def sync(self, ctx) -> None:
        fmt = await ctx.bot.tree.sync(guild=discord.Object(GUILD_ID))
        await ctx.send(f"synced {len(fmt)} commands")

    # Remove referrer from DB by ID
    @commands.command(help="remove_referrer", description="Remove referrer from DB by ID")
    @commands.has_any_role("Owner", "Admin")
    async def remove_referrer(self, ctx: discord.ext.commands.context.Context, user_id: str) -> None:
        descending = "DELETE FROM invites WHERE user_id = ?"
        cursor.execute(descending, (user_id,))
        database.commit()
        await ctx.send(f"Referrer <@{user_id}> removed from db")

    # Remove data from activity_giveaway table
    @commands.command(help="reset_activity_giveaway", description="Remove data from activity_giveaway table")
    @commands.has_any_role("Owner", "Admin")
    async def reset_activity_giveaway(self, ctx: discord.ext.commands.context.Context) -> None:
        descending = "DELETE FROM activity_giveaway"
        cursor.execute(descending)
        database.commit()
        await ctx.send(f"Activity giveaway was reset!")

    # Add exp to user_id
    @commands.command(help="add_exp", description="Add exp to user_id")
    @commands.has_any_role("Owner", "Admin")
    async def add_exp(self, ctx: discord.ext.commands.context.Context, user_id: str, add_exp: str) -> None:
        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                       f"{user_id} and guild_id = {ctx.guild.id}")
        activity_giveaway_result = cursor.fetchone()

        if activity_giveaway_result is None:
            cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                           f"VALUES({user_id}, {ctx.guild.id}, {int(add_exp)}, 0, 0)")
            database.commit()

            await ctx.send(f"Set {add_exp} exp to <@{user_id}>")
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

            await ctx.send(f"Added {add_exp} exp to <@{user_id}>. Now he have {exp} exp.")

    # Reduce exp to user_id
    @commands.command(help="reduce_exp", description="Reduce exp to user_id")
    @commands.has_any_role("Owner", "Admin")
    async def reduce_exp(self, ctx: discord.ext.commands.context.Context, user_id: str, reduce_exp: str) -> None:
        cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                       f"{user_id} and guild_id = {ctx.guild.id}")
        activity_giveaway_result = cursor.fetchone()

        if activity_giveaway_result is None:
            cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                           f"VALUES({user_id}, {ctx.guild.id}, 0, 0, 0)")
            database.commit()

            await ctx.send(f"<@{user_id}> have 0 exp.")
        else:
            user_id, guild_id, exp, level, last_lvl = activity_giveaway_result

            # Reduce XP
            exp_gained = int(reduce_exp)
            exp -= exp_gained
            if exp < 0:
                exp = 0
            level = 0.1 * (math.sqrt(exp))

            cursor.execute(
                f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                f"guild_id = {guild_id}")
            database.commit()

            await ctx.send(f"Reduced {reduce_exp} exp to <@{user_id}>. Now he have {exp} exp.")

    # Command for send message from Bot
    @commands.command(help="send_message", description="Command for send message from Bot")
    @commands.has_any_role("Owner", "Admin")
    async def send_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message: str) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("message: ", message)
        await channel.send(content=message)

    # Command for send file from Bot
    @commands.command(help="send_file", description="Command for send file from Bot")
    @commands.has_any_role("Owner", "Admin")
    async def send_file(self, ctx: discord.ext.commands.context.Context, channel_id: str,
                        file: discord.Attachment) -> None:
        channel = await self.client.fetch_channel(channel_id)
        print("channel_id: ", channel_id)
        print("file: ", file)
        await channel.send(file=await file.to_file())

    # Command for send message with file from Bot
    @commands.command(help="send_embed_message", description="Command for send message with file from Bot")
    @commands.has_any_role("Owner", "Admin")
    async def send_embed_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message: str,
                                 file: discord.Attachment) -> None:
        channel = await self.client.fetch_channel(channel_id)
        await channel.send(content=message, file=await file.to_file())

    # Command for edit file in message from Bot
    @commands.command(help="edit_file", description="Command for edit file in message from Bot")
    @commands.has_any_role("Owner", "Admin")
    async def edit_file(self, ctx: discord.ext.commands.context.Context, channel_id: str, message_id: str) -> None:

        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        files: [discord.File] = []

        for file in ctx.message.attachments:
            files.append(await file.to_file())

        await message.edit(attachments=files)

    # Command for edit message from Bot
    @commands.command(help="edit_message", description="Command for edit message from Bot")
    @commands.has_any_role("Owner", "Admin")
    async def edit_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message_id: str,
                           message_text: str) -> None:
        channel = await self.client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        await message.edit(content=message_text)

    # Command for edit message with file from Bot
    @commands.command(help="edit_embed_message", description="Command for edit message with file from Bot")
    @commands.has_any_role("Owner", "Admin")
    async def edit_embed_message(self, ctx: discord.ext.commands.context.Context, channel_id: str, message_id: str,
                                 message_text: str) -> None:
        channel = await self.client.fetch_channel(channel_id)

        files: [discord.File] = []

        for file in ctx.message.attachments:
            files.append(await file.to_file())

        message = await channel.fetch_message(message_id)

        await message.edit(content=message_text, attachments=files)

    # Command for add manually join user log in log channel
    @commands.command(help="join_user", description="Command for add manually join user log in log channel")
    @commands.has_any_role("Owner", "Admin")
    async def join_user(self, member_id, user_id) -> None:
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            description=f":wave: Welcome to server **<@{user_id}>**!",
            color=0x4caf50,
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)

    # Command for get members dict() by message_id who reacted on post
    @commands.command(help="get_members_list", description="Command for get members dict() by message_id who reacted on post")
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
    @commands.command(help="giveaway_random", description="Command for get random winner from message reactions")
    @commands.has_any_role("Owner", "Admin")
    async def giveaway_random(self, ctx, count, message_id, message_id2: str = None, repeat: str = None) -> None:
        await ctx.send(f"Participants of the competition.")
        get_all_reacted_users = await self.get_members_list(ctx, message_id)
        if message_id2:
            get_all_reacted_users = get_all_reacted_users.union(await self.get_members_list(ctx, message_id2))

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
