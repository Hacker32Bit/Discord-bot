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
	"invited_by"	INTEGER NOT NULL UNIQUE,
	PRIMARY KEY("user_id")
);""")


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
    async def on_member_join(self, member) -> None:

        is_invited = False
        inviter = None

        # Getting the invites before the user joining
        # from our cache for this specific guild

        print("OnMemberJoin", member.guild.id)
        invites_before_join = self.invites[member.guild.id]

        # Getting the invites after the user joining
        # so we can compare it with the first one, and
        # see which invite uses number increased

        invites_after_join = await member.guild.invites()

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

                if not result:
                    is_invited = True
                    inviter = invite.inviter.mention
                    invited_by = invite.inviter.id
                    cursor.execute(f"INSERT INTO invites(user_id, invited_by) "
                                   f"VALUES({member.id}, {invited_by});")
                    database.commit()


        # Send message in LOG_CHANNEL if not invited
        channel = await self.client.fetch_channel(LOG_CHANNEL_ID)

        if is_invited:
            embed = discord.Embed(
                description=f":wave: Welcome to server **{member.mention}**!\nReferred by **{inviter}**!",
                color=0x9b59b6,
                timestamp=datetime.datetime.now()
            )
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
