from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Ping\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Ping\" was unloaded!")

    # Ping
    @commands.command(help="Returns bot latency")
    @commands.has_any_role("Admin", "Owner")
    async def ping(self, ctx):
        bot_latency = round(self.client.latency * 1000)

        await ctx.send(f"Pong! {bot_latency} ms.")


async def setup(client):
    await client.add_cog(Ping(client))
