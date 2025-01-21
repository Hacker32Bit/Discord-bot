import discord
from discord.ext import commands
import datetime
from dotenv import load_dotenv
from typing import Final
import os


load_dotenv()
LOG_CHANNEL_ID: Final[str] = os.getenv("LOG_CHANNEL_ID")
GUILD_ID = Final[int] = os.getenv("GUILD_ID")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")


class MemberUpdate(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.invites = {}


    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Member update\" cog is ready!")
        for guild in self.client.guilds:
            # Adding each guild's invites to our dict
            self.invites[guild.id] = await guild.invites()
        print("OnReady", self.invites)

    @staticmethod
    async def find_invite_by_code(invite_list, code):
        # Simply looping through each invite in an
        # invite list which we will get using guild.invites()
        for inv in invite_list:
            # Check if the invite code in this element
            # of the list is the one we're looking for
            if inv.code == code:
                # If it is, we return it.
                return inv

    @commands.Cog.listener()
    async def on_member_join(self, member):

        # Getting the invites before the user joining
        # from our cache for this specific guild

        print("OnMemberJoin", member.guild.id)
        invites_before_join = self.invites[GUILD_ID]

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

                self.invites[GUILD_ID] = invites_after_join

                # We return here since we already found which
                # one was used and there is no point in
                # looping when we already got what we wanted

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Updates the cache when a user leaves to make sure
        # everything is up to date
        self.invites[GUILD_ID] = await member.guild.invites()

    # Called when member update
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Give role when joined
        if before.pending and not after.pending:
            role = discord.utils.get(before.guild.roles, name="Member")
            await after.add_roles(role)

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

    # Called when member presence update
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):

        if before and after and before.status != after.status:  # logging your member's status
            description = (
                f"**{before.mention}**'s status changed!\n"
                f"From **{before.status}** to **{after.status}**!")
            embed = discord.Embed(
                description=description,
                color=0xcddc39 if after.status == "online" else 0xff9800,
                timestamp=datetime.datetime.now()
            )
            channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)  # admin log channel
            await channel.send(embed=embed)

        if before and after and before.activity != after.activity:  # logging you member's activities
            description = (
                f"**{before.mention}**'s activity changed!\n"
                f"From **{before.activity.name}** to **{after.activity.name}**!")
            embed = discord.Embed(
                description=description,
                color=0xcddc39,
                timestamp=datetime.datetime.now()
            )
            channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)  # admin log channel
            await channel.send(embed=embed)


async def setup(client):
    await client.add_cog(MemberUpdate(client))
