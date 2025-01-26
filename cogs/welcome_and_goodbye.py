import math
import sqlite3

import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os


load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")


database = sqlite3.connect("database.sqlite")
cursor = database.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS "invites" (
	"user_id"	INTEGER NOT NULL UNIQUE,
	"invited_by"	INTEGER NOT NULL,
	PRIMARY KEY("user_id")
)""")


class WelcomeAndGoodbye(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.invites = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Welcome & Goodbye\" cog is ready!")
        for guild in self.client.guilds:
            # Adding each guild's invites to our dict
            self.invites[guild.id] = await guild.invites()
        print("on_ready", self.invites)

    @staticmethod
    def find_invite_by_code(invite_list, code):
        # Simply looping through each invite in an
        # invite list which we will get using guild.invites()
        for inv in invite_list:
            # Check if the invite code in this element
            # of the list is the one we're looking for
            if inv.code == code:
                # If it is, we return it.
                return inv

    @commands.Cog.listener()
    async def on_guild_update(self, before, after) -> None:
        print(self)
        print(type(before))
        print(before)
        print(after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:

        inviter = None
        invited_by = None

        # Getting the invites before the user joining
        # from our cache for this specific guild

        print("OnMemberJoin", member.guild.id)
        invites_before_join = self.invites[member.guild.id]
        print(invites_before_join)

        # Getting the invites after the user joining
        # so we can compare it with the first one, and
        # see which invite uses number increased

        invites_after_join = await member.guild.invites()
        print(invites_after_join)


        # Loops for each invite we have for the guild
        # the user joined.

        for invite in invites_before_join:

            # Now, we're using the function we created just
            # before to check which invite count is bigger
            # than it was before the user joined.

            if invite.uses < self.find_invite_by_code(invites_after_join, invite.code).uses:
                # Now that we found which link was used,
                # we will print a couple things in our console:
                # the name, invite code used the the person
                # who created the invite code, or the inviter.

                print(f"Member {member.name} Joined")
                print(f"Invite Code: {invite.code}")
                print(f"Inviter: {invite.inviter}")

                # We will now update our cache so it's ready
                # for the next user that joins the guild

                self.invites[member.guild.id] = invites_after_join

                # We return here since we already found which
                # one was used and there is no point in
                # looping when we already got what we wanted

                cursor.execute(f"SELECT user_id, invited_by FROM invites WHERE user_id = "
                       f"{member.id}")
                result = cursor.fetchone()

                print("db query result: ", result)

                if not result:
                    inviter = invite.inviter.mention
                    invited_by = invite.inviter.id
                    cursor.execute(f"INSERT INTO invites(user_id, invited_by) "
                                   f"VALUES({member.id}, {invited_by});")
                    database.commit()

        # Send message in LOG_CHANNEL if not invited
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)

        print("inviter: ", inviter)
        print("invited_by: ", invited_by)

        if inviter and invited_by:
            embed = discord.Embed(
                description=f":wave: Welcome to server **{member.mention}**!\nReferred by **{inviter}**!",
                color=0x9b59b6,
                timestamp=datetime.datetime.now()
            )
            await channel.send(embed=embed)

            cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM activity_giveaway WHERE user_id = "
                           f"{invited_by} and guild_id = {member.guild.id}")
            activity_giveaway_result = cursor.fetchone()

            if activity_giveaway_result is None:
                cursor.execute(f"INSERT INTO activity_giveaway(user_id, guild_id, exp, level, last_lvl) "
                               f"VALUES({invited_by}, {member.guild.id}, 0, 0, 0)")
                database.commit()
            else:
                user_id, guild_id, exp, level, last_lvl = activity_giveaway_result

                # Give 150 XP for invite
                exp_gained = 150
                exp += exp_gained
                level = 0.1 * (math.sqrt(exp))

                cursor.execute(
                    f"UPDATE activity_giveaway SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                    f"guild_id = {guild_id}")
                database.commit()

            cursor.execute(f"SELECT user_id, guild_id, exp, level, last_lvl FROM levels WHERE user_id = "
                           f"{invited_by} and guild_id = {member.guild.id}")
            leveling_result = cursor.fetchone()

            if leveling_result is None:
                cursor.execute(f"INSERT INTO levels(user_id, guild_id, exp, level, last_lvl, background) "
                               f"VALUES({invited_by}, {member.guild.id}, 150, 0, 0, 0)")
                database.commit()
            else:
                user_id, guild_id, exp, level, last_lvl = leveling_result

                exp_gained = 150
                exp += exp_gained
                level = 0.1 * (math.sqrt(exp))

                cursor.execute(f"UPDATE levels SET exp = {exp}, level = {level} WHERE user_id = {user_id} AND "
                               f"guild_id = {guild_id}")
                database.commit()

                if int(level) > last_lvl:
                    cursor.execute(f"UPDATE levels SET last_lvl = {int(level)} WHERE user_id = {user_id} AND "
                                   f"guild_id = {guild_id}")
                    database.commit()

                    user = member.guild.get_member(invited_by)

                    if int(level) == 5:
                        role = discord.utils.get(member.guild.roles, name="Beginner (5 LVL)")
                        await user.add_roles(role)
                    elif int(level) == 10:
                        role = discord.utils.get(member.guild.roles, name="Beginner (5 LVL)")
                        await user.remove_roles(role)
                        role = discord.utils.get(member.guild.roles, name="Intermediate (10 LVL)")
                        await user.add_roles(role)
                    elif int(level) == 15:
                        role = discord.utils.get(member.guild.roles, name="Intermediate (10 LVL)")
                        await user.remove_roles(role)
                        role = discord.utils.get(member.guild.roles, name="Advanced (20 LVL)")
                        await user.add_roles(role)
                    elif int(level) == 25:
                        role = discord.utils.get(member.guild.roles, name="Advanced (20 LVL)")
                        await user.remove_roles(role)
                        role = discord.utils.get(member.guild.roles, name="Expert (30 LVL)")
                        await user.add_roles(role)
                    elif int(level) == 50:
                        role = discord.utils.get(member.guild.roles, name="Expert (30 LVL)")
                        await user.remove_roles(role)
                        role = discord.utils.get(member.guild.roles, name="Elite (40 LVL)")
                        await user.add_roles(role)
                    elif int(level) == 100:
                        role = discord.utils.get(member.guild.roles, name="Elite (40 LVL)")
                        await user.remove_roles(role)
                        role = discord.utils.get(member.guild.roles, name="Godly (50 LVL)")
                        await user.add_roles(role)

                    await channel.send(f"{inviter} has leveled up to level {int(level)}!")
        else:
            embed = discord.Embed(
                description=f":wave: Welcome to server **{member.mention}**!",
                color=0x4caf50,
                timestamp=datetime.datetime.now()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member) -> None:
        # Updates the cache when a user leaves to make sure
        # everything is up to date
        self.invites[member.guild.id] = await member.guild.invites()

        # Send message in LOG_CHANNEL
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)
        embed = discord.Embed(
            description=f"<:hmm2:1240238779181174825> **{member.mention}** leaved from this server!",
            color=0xff9800,
            timestamp=datetime.datetime.now()
        )
        await channel.send(embed=embed)


async def setup(client):
    await client.add_cog(WelcomeAndGoodbye(client))
