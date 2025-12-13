import asyncio
import os
import datetime
from typing import Final
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
VOICE_CHANNELS_GROUP_ID: Final[str] = os.getenv("VOICE_CHANNELS_GROUP_ID")
STAFF_CHANNELS_GROUP_ID: Final[str] = os.getenv("STAFF_CHANNELS_GROUP_ID")
MEETING_VOICE_CHANNEL_ID: Final[str] = os.getenv("MEETING_VOICE_CHANNEL_ID")
AFK_VOICE_CHANNEL_ID: Final[str] = os.getenv("AFK_VOICE_CHANNEL_ID")
MUSIC_VOICE_CHANNEL_ID: Final[str] = os.getenv("MUSIC_VOICE_CHANNEL_ID")
STREAMS_VOICE_CHANNEL_ID: Final[str] = os.getenv("STREAMS_VOICE_CHANNEL_ID")
GENERAL_VOICE_CHANNEL_ID: Final[str] = os.getenv("GENERAL_VOICE_CHANNEL_ID")


class AutoChannel(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Auto Channel\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Auto Channel\" was unloaded!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before and before.channel is not None:
            if str(before.channel.id) in [GENERAL_VOICE_CHANNEL_ID, STREAMS_VOICE_CHANNEL_ID, MUSIC_VOICE_CHANNEL_ID,
                                          AFK_VOICE_CHANNEL_ID, MEETING_VOICE_CHANNEL_ID]:
                pass
            else:
                if not len(before.channel.members):
                    await before.channel.delete(reason="Channel was empty")

        if after and after.channel and str(after.channel.category_id) in [VOICE_CHANNELS_GROUP_ID,
                                                                          STAFF_CHANNELS_GROUP_ID]:
            if after.channel.name == "〔🤝〕Face-to-Face":
                # Get channels from category_id
                category = discord.utils.get(member.guild.categories, id=after.channel.category_id)
                channels = category.channels

                # Filter channels and get channel_numbers
                channel_numbers = []
                channel_id = 1
                for channel in channels:
                    if channel.name in ["〔💬〕chat", "〔🔊〕General", "〔📷〕Streams", "〔🎵〕Music", "〔💤〕AFK",
                                        "〔🤝〕Face-to-Face", "〔📁〕assets", "〔📁〕logs", "〔🤖〕commands",
                                        "〔💬〕general", "〔🦜〕spam", "〔🤝〕Meeting"]:
                        continue
                    elif channel.name.split()[1][1:]:
                        channel_numbers.append(int(channel.name.split()[1][1:]))

                if channel_numbers:
                    channel_numbers.sort(reverse=False)

                    for index in range(1, channel_numbers[-1] + 2):
                        if index not in channel_numbers:
                            channel_id = index
                            break

                pos = after.channel.position
                new_channel = await after.channel.clone(name="〔🤝〕Face-to-Face",
                                                        reason=f"Created new Face-to-Face #{channel_id} channel by "
                                                               f"{member.name}.")
                await asyncio.sleep(1)

                await after.channel.edit(name=f"〔🤝〕Face-to-Face #{channel_id}", user_limit=2)
                embed = discord.Embed(
                    description=f"Congrats {member.name}! You have created a new\n〔🤝〕Face-to-Face channel.",
                    color=0x9c27b0,
                    timestamp=datetime.datetime.now()
                )
                await after.channel.send(f"Welcome to〔🤝〕 Face-To-Face channel {member.mention}", embed=embed)

                await asyncio.sleep(1)
                await new_channel.edit(user_limit=0, position=pos)

                embed = discord.Embed(
                    description=f"Note!!!\nThis lobby are temporary!!!\nIf lobby will empty, it delete automatically "
                                f"with messages!",
                    color=0xFF9800
                )
                await after.channel.send(embed=embed)

        else:
            # Create new channel when joined on empty channel.
            if after and after.channel and after.channel.name == "〔🎮〕Create lobby!":
                # Get channels from category_id
                category = discord.utils.get(member.guild.categories, id=after.channel.category_id)
                channels = category.channels

                # Filter channels and get channel_numbers
                channel_numbers = []
                channel_id = 1
                for channel in channels:
                    if channel.name == "〔💬〕chat":
                        continue
                    elif channel.name == "〔🎮〕Create lobby!":
                        continue
                    elif channel.name.split()[1][1:]:
                        channel_numbers.append(int(channel.name.split()[1][1:]))

                if channel_numbers:
                    channel_numbers.sort(reverse=False)

                    for index in range(1, channel_numbers[-1] + 2):
                        if index not in channel_numbers:
                            channel_id = index
                            break

                new_channel = await after.channel.clone(name="〔🎮〕Create lobby!",
                                                        reason=f"Created new lobby #{channel_id} by {member.name}.")
                await asyncio.sleep(1)

                await after.channel.edit(name=f"〔🎮〕New #{channel_id}", user_limit=1)

                embed = discord.Embed(
                    description=f"Congrats {member.name}! You have created a new lobby.",
                    color=0x9c27b0,
                    timestamp=datetime.datetime.now()
                )
                await after.channel.send(f"Welcome to new lobby! {member.mention}", embed=embed)

                embed = discord.Embed(
                    description="Now your lobby closed for everyone.\nLet's configure your lobby now.",
                    color=0xf44336
                )
                await after.channel.send(embed=embed)

                embed = discord.Embed(
                    description="Set lobby limits for members. \nEnter a number between 2-99.\n"
                                "If you want Unlimited lobby, enter 0.",
                    color=0xffc107
                )
                await after.channel.send(embed=embed)

                await asyncio.sleep(1)
                await new_channel.edit(user_limit=0, position=1)

                def check(m):  # checking if it's the same user and channel
                    return m.author == member and m.channel.voice_states[member.id] == after

                channel_size = 0

                while True:
                    try:  # waiting for message
                        # timeout - how long bot waits for message (in seconds)
                        response = await self.client.wait_for("message", check=check, timeout=300.0)

                    except asyncio.TimeoutError:
                        await after.channel.delete(reason="Timed!")
                        return

                    try:
                        channel_size = int(response.content)
                        if channel_size not in range(0, 99) or channel_size == 1:
                            embed = discord.Embed(
                                description="Number not in range.\nPlease, write a number between 2-99 or 0!\n",
                                color=0xf44336
                            )
                            await after.channel.send(embed=embed)
                            continue
                    except ValueError:
                        embed = discord.Embed(
                            description="Wrong answer!\nPlease, write a number between 2-99 or 0!\n",
                            color=0xf44336
                        )
                        await after.channel.send(embed=embed)
                        continue

                    break

                if channel_size:
                    limit = 'limited lobby by ' + str(channel_size) + ' members.'
                    await after.channel.edit(name=f"〔🎮〕Lobby #{channel_id}", user_limit=channel_size)
                else:
                    limit = 'unlimited lobby.'
                    await after.channel.edit(name=f"〔🎮〕Lobby #{channel_id}", user_limit=0)

                embed = discord.Embed(
                    description=f"Great!\nYou configured {limit}\nHave fun!",
                    color=0x4caf50
                )
                await after.channel.send(embed=embed)

                embed = discord.Embed(
                    description=f"Note!!!\nThis lobby are temporary!!!\nIf lobby will empty, it delete automatically "
                                f"with messages!",
                    color=0xFF9800
                )
                await after.channel.send(embed=embed)


async def setup(client):
    await client.add_cog(AutoChannel(client))
