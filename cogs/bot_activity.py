import datetime
import os
from typing import Final

import discord
import requests
from time import sleep
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

load_dotenv()
GUILD_ID: Final[str] = os.getenv("GUILD_ID")
STREAMS_VOICE_CHANNEL_ID: Final[str] = os.getenv("STREAMS_VOICE_CHANNEL_ID")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")


class BotActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_monitor_task = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Bot activity\" cog is ready!")
        status = discord.CustomActivity(name="I'm free...")
        await self.bot.change_presence(status=discord.Status.idle, activity=status)
        self.bot.current_activity = status

        # text = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."""
        #
        # text_length = len(text)
        # current_time = datetime.datetime.now(datetime.timezone.utc)
        # tomorrow = current_time.date() + datetime.timedelta(days=1)
        # target_datetime = datetime.datetime.combine(tomorrow, datetime.time(2, 0, 0, tzinfo=datetime.timezone.utc))
        # total_seconds = (target_datetime - current_time).total_seconds()
        # print(total_seconds)
        # timeout = total_seconds / text_length
        #
        # for letter in text:
        #     await asyncio.sleep(timeout)
        #     await self.bot.change_presence(
        #         activity=discord.Activity(type=discord.ActivityType.watching, name=format(ord(letter), '08b')),
        #         status=discord.Status.idle)

    async def cog_load(self):
        # Called automatically when the cog is loaded
        # self.voice_monitor_task = asyncio.create_task(self.monitor_connection())
        print("[INFO] Cog \"Bot Activity\" was loaded!")

    def cog_unload(self):
        print("[INFO] Cog \"Bot Activity\" was unloaded!")

    async def join_voice_channel(self):
        log_channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)

        try:
            channel = self.bot.get_channel(STREAMS_VOICE_CHANNEL_ID)
            if channel is None:
                channel = await self.bot.fetch_channel(STREAMS_VOICE_CHANNEL_ID)

            if isinstance(channel, discord.VoiceChannel):
                vc = channel.guild.voice_client
                if vc is None or not vc.is_connected():
                    await channel.connect()
                    await log_channel.send(content=f"✅ Connected to {channel.name}")
        except Exception as e:
            await log_channel.send(content=f"❌ Failed to join voice channel: \n```{e}```")

    async def monitor_connection(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.join_voice_channel()
            await asyncio.sleep(60)  # Check every 60 seconds

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        username: str = str(message.author)
        user_message: str = message.content
        channel: str = str(message.channel)

        if message.author == self.bot.user:
            return

        if user_message.lower() in ["чат", "watch", "follow", "gpt", "chat"]:
            activity = getattr(self.bot, "current_activity", None)

            if str(activity) == "I'm ready to discuss":
                status = discord.CustomActivity(name="I'm free...")
                await self.bot.change_presence(status=discord.Status.idle, activity=status)
                self.bot.current_activity = status
            else:
                status = discord.CustomActivity(name="I'm ready to discuss")
                await self.bot.change_presence(status=discord.Status.online, activity=status)
                self.bot.current_activity = status

        # # Setting `Playing ` status
        # await bot.change_presence(activity=discord.Game(name="a game"))
        #
        # # Setting `Streaming ` status
        # await bot.change_presence(activity=discord.Streaming(name="My Stream", url=my_twitch_url))
        #
        # # Setting `Listening ` status
        # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="a song"))
        #
        # # Setting `Watching ` status
        # await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))


async def setup(bot):
    await bot.add_cog(BotActivity(bot), guilds=[discord.Object(id=GUILD_ID)])
