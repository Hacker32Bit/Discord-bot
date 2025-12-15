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
    async def help_command(self, ctx, *, arg: str = None):
        if arg is None:
            categories = defaultdict(list)

            for command in self.bot.commands:
                if not command.hidden:
                    # Use cog name or fallback to 'No Category'
                    category = command.cog_name or "No Category"
                    categories[category].append(command)

            # Build help message
            lines = ["\nType [2;32m!help command[0m for more info on a command.",
                     "You can also type [2;32m!help category[0m for more info on a category."]

            await ctx.send(f"```ansi\n{chr(10).join(lines)}\n```")

            for category, commands_list in categories.items():
                lines.clear()
                lines.append(f"\n [1;2m[1;35m{category}[0m:[0m")
                for cmd in commands_list:
                    name = cmd.name
                    short_help = cmd.help if cmd.help else name
                    lines.append(f"  [2;32m{ctx.prefix}{name:<23} [0m{short_help}")
                await ctx.send(f"```ansi\n{chr(10).join(lines)}\n```")
        else:
            # Try to find command
            command = self.bot.get_command(arg)
            if command and not command.hidden:
                aliases = ", ".join(command.aliases) if command.aliases else "None"
                usage = f"{ctx.prefix}{command.qualified_name} {command.signature}".strip()

                lines = [
                    f"Command: {ctx.prefix}{command.name}",
                    f"Description: {command.help or 'No description'}",
                    f"Usage: {usage}",
                    f"Aliases: {aliases}"
                ]
                await ctx.send(f"```\n{chr(10).join(lines)}\n```")
                return

            # Try to find category (cog)
            matched_category = None
            for cog in self.bot.cogs.values():
                if cog.qualified_name.lower() == arg.lower():
                    matched_category = cog
                    break

            if matched_category:
                commands_list = [
                    cmd for cmd in matched_category.get_commands() if not cmd.hidden
                ]
                if not commands_list:
                    await ctx.send(f"```ansi\n[2;31mNo visible commands found in category [2;35m{arg}[0m[2;31m.[0m```")
                    return

                lines = [f"{matched_category.qualified_name} Commands:"]
                for cmd in commands_list:
                    cmd_name = f"{ctx.prefix}{cmd.name}"
                    short_help = cmd.help or cmd.name
                    lines.append(f"  [2;32m{cmd_name:<24} [0m{short_help}")

                await ctx.send(f"```ansi\n{chr(10).join(lines)}\n```")
                return

            # Nothing matched
            await ctx.send(f"```ansi\n[2;31mNo command or category found for [2;37m{arg}[0m[2;31m.[0m```")

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
