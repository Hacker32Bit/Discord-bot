from discord.ext import commands
from demoparser2 import DemoParser

class WatchDemoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Watch Demo\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Watch Demo\" was unloaded!")

    @commands.command(name="watch_demo", help="Analyze cs2 demo")
    @commands.has_any_role("Owner", "Admin")
    async def watch_demo(self, ctx, demo_url: str = ""):
        path = "/home/gektor/demo.dem"

        parser = DemoParser(path)
        players = parser.parse_player_info()

        await ctx.send(f"Current url: {demo_url}\nDemo info:\n```{players}```")

async def setup(bot):
    await bot.add_cog(WatchDemoCog(bot))
