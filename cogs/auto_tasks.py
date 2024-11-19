import datetime
from discord.ext import commands, tasks


utc = datetime.timezone.utc
# If no tzinfo is given then UTC is assumed.
time = datetime.time(hour=13, minute=50, tzinfo=utc)


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(time=time)
    async def my_task(self):
        pass
        # print("Need close server!")


async def setup(client):
    await client.add_cog(MyCog(client))
