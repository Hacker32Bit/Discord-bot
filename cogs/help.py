from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Help\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Help\" was unloaded!")

    @commands.command(name="help", description="Returns all commands available")
    @commands.has_any_role("Owner", "Admin")
    async def help(self, ctx):
        helptext = "```Available Commands:\n"
        for command in self.bot.commands:
            if not command.hidden:
                helptext += f"{ctx.prefix}{command.name} - {command.help or 'No description'}\n"
        helptext += "```"
        await ctx.send(helptext)

def setup(bot):
    bot.add_cog(HelpCog(bot))
