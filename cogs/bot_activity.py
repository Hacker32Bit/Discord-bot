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

class BotActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client = None
        self.bot.loop.create_task(self.join_voice_channel())
        self.bot.loop.create_task(self.monitor_connection())

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Bot activity\" cog is ready!")
        status = discord.CustomActivity(name="I'm free...")
        await self.bot.change_presence(status=discord.Status.idle, activity=status)

    async def join_voice_channel(self):
        await self.bot.wait_until_ready()
        channel = await self.bot.fetch_channel(STREAMS_VOICE_CHANNEL_ID)
        if isinstance(channel, discord.VoiceChannel):
            if not channel.guild.voice_client:
                self.voice_client = await channel.connect()

    async def monitor_connection(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            channel = await self.bot.fetch_channel(STREAMS_VOICE_CHANNEL_ID)
            if isinstance(channel, discord.VoiceChannel):
                vc = channel.guild.voice_client
                if not vc or not vc.is_connected():
                    try:
                        await channel.connect()
                    except Exception as e:
                        print(f"Reconnect failed: {e}")
            await asyncio.sleep(60)  # check every minute

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        username: str = str(message.author)
        user_message: str = message.content
        channel: str = str(message.channel)

        print(f"[{channel}] {username}: {user_message}")

        if message.author == self.bot.user:
            return

        if user_message.lower() == "game":
            try:
                top_games_url = "https://steamdb.info/stats/trendingfollowers/"
                r = requests.get(top_games_url)
                while r.status_code == 429:
                    print("Page is not loaded! Retrying after 10 seconds...")
                    sleep(10)
                    r = requests.get(top_games_url)

            except Exception as err:
                print(err)

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
