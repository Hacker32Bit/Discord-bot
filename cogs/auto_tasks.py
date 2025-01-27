import datetime
import os
from typing import Final

from discord.ext import commands, tasks


utc = datetime.timezone.utc
# If no tzinfo is given then UTC is assumed.
time = datetime.time(hour=13, minute=50, tzinfo=utc)

ACTIVITY_GIVEAWAY_CHANNEL_ID: Final[str] = os.getenv("ACTIVITY_GIVEAWAY_CHANNEL_ID")
ACTIVITY_GIVEAWAY_MESSAGE_ID: Final[str] = os.getenv("ACTIVITY_GIVEAWAY_MESSAGE_ID")


class AutoTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()
        self.update_activity_giveaways_tables.start()

    def cog_unload(self):
        self.my_task.cancel()
        self.update_activity_giveaways_tables.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"AutoTask\" cog is ready!")

    @tasks.loop(time=time)
    async def my_task(self):
        pass
        # print("Need close server!")

    @tasks.loop(minutes=1)
    async def update_activity_giveaways_tables(self):
        channel = self.bot.get_channel(ACTIVITY_GIVEAWAY_CHANNEL_ID)
        message = await channel.fetch_message(ACTIVITY_GIVEAWAY_MESSAGE_ID)

        if not message:
            print("NO MESSAGES")

        await message.edit(content="the new content of the message")
        print("UPDATE!!!")


async def setup(bot):
    await bot.add_cog(AutoTask(bot))
