from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Help\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Help\" was unloaded!")

    @commands.command(name="help", help="Shows all available commands")
    @commands.has_any_role("Owner", "Admin")
    async def help_command(self, ctx):
        helptext = "```ansi\nAvailable Commands:\n"
        for command in self.bot.commands:
            if not command.hidden:
                helptext += f"[2;32m{ctx.prefix}{command.name}[0m - {command.help or 'No description'}\n"

        helptext += "```"
        await ctx.send(helptext)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
