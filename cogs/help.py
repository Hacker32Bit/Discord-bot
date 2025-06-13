from discord.ext import commands
from collections import defaultdict

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
        categories = defaultdict(list)

        for command in self.bot.commands:
            if not command.hidden:
                # Use cog name or fallback to 'No Category'
                category = command.cog_name or "No Category"
                categories[category].append(command)

        # Build help message
        lines = ["\nType [2;32m!help command[0m for more info on a command.",
                 "You can also type [2;32m!help category[0m for more info on a category."]

        for category, commands_list in categories.items():
            lines.append(f"\n [1;2m[1;35m{category}[0m:[0m")
            for cmd in commands_list:
                name = cmd.name
                short_help = cmd.help if cmd.help else name
                lines.append(f"  [2;32m{name:<24} [0m{short_help}")

        await ctx.send(f"```ansi\n{chr(10).join(lines)}\n```")

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
