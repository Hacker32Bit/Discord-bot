import datetime
from discord.ext import commands, tasks


utc = datetime.timezone.utc
# If no tzinfo is given then UTC is assumed.
time = datetime.time(hour=13, minute=50, tzinfo=utc)


class AutoTask(commands.Cog):
    def __init__(self, client):
        self.client = client
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
        print("UPDATE!!!")


async def setup(client):
    await client.add_cog(AutoTask(client))
