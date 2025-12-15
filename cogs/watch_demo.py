from discord.ext import commands
import discord
from demoparser2 import DemoParser
from dotenv import load_dotenv
from typing import Final
import os

load_dotenv()
STEAM_API_KEY: Final[str] = os.getenv("STEAM_API_KEY")
FACEIT_API_KEY: Final[str] = os.getenv("FACEIT_API_KEY")

# Example data (replace with real Steam profiles)
STEAM_PROFILES = [
    {"name": "Profile 1", "steam_id": "76561199234124671"},
    {"name": "Profile 2", "steam_id": "76561198812258436"},
    {"name": "Profile 3", "steam_id": "76561199527201188"},
    {"name": "Profile 4", "steam_id": "76561199231739701"},
    {"name": "Profile 5", "steam_id": "76561198981314495"},
    {"name": "Profile 6", "steam_id": "76561199519970864"},
    {"name": "Profile 7", "steam_id": "76561199027104248"},
    {"name": "Profile 8", "steam_id": "76561199245723353"},
    {"name": "Profile 9", "steam_id": "76561199555592308"},
    {"name": "Profile 10", "steam_id": "76561198176135483"},
]

class ProfileToggleView(discord.ui.View):
    def __init__(self, author: discord.User, profiles: list[dict]):
        super().__init__(timeout=120)
        self.author = author
        self.profiles = profiles

        # steam_id -> bool
        self.state = {p["steam_id"]: False for p in profiles}

        for index, profile in enumerate(profiles):
            self.add_item(ProfileToggleButton(profile, index))

        self.add_item(DoneButton())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ This interaction is not for you.",
                ephemeral=True
            )
            return False
        return True


class ProfileToggleButton(discord.ui.Button):
    def __init__(self, profile: dict, index: int):
        super().__init__(
            label=profile["name"],
            style=discord.ButtonStyle.secondary,
            emoji="🔇",
            row=index // 5
        )
        self.profile = profile

    async def callback(self, interaction: discord.Interaction):
        view: ProfileToggleView = self.view  # type: ignore

        steam_id = self.profile["steam_id"]
        view.state[steam_id] = not view.state[steam_id]

        enabled = view.state[steam_id]

        self.style = (
            discord.ButtonStyle.success if enabled
            else discord.ButtonStyle.secondary
        )
        self.emoji = "🔊" if enabled else "🔇"

        await interaction.response.edit_message(view=view)


class DoneButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Done",
            style=discord.ButtonStyle.primary,
            emoji="📤",
            row=2
        )

    async def callback(self, interaction: discord.Interaction):
        view: ProfileToggleView = self.view  # type: ignore

        selected = [
            steam_id for steam_id, enabled in view.state.items() if enabled
        ]

        # Send result (or save to DB / cache)
        await interaction.response.send_message(
            f"✅ Selected Steam IDs:\n" + "\n".join(selected),
            ephemeral=True
        )

        # Disable all buttons after submit
        for item in view.children:
            item.disabled = True

        await interaction.message.edit(view=view)
        view.stop()


class WatchDemoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Watch Demo\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Watch Demo\" was unloaded!")

    @commands.command(help="watch_demo_test", description="Test feature")
    @commands.has_any_role("Owner", "Admin")
    async def watch_demo_test(self, ctx: commands.Context):
        """Show Steam profiles with checkbox buttons"""
        view = ProfileToggleView(ctx.author, STEAM_PROFILES)

        await ctx.send(
            "Select Steam profiles:",
            view=view
        )

    @commands.command(help="watch_demo", description="Analyze cs2 demo")
    @commands.has_any_role("Owner", "Admin")
    async def watch_demo(self, ctx, demo_url: str = ""):
        path = "/home/gektor/demo.dem"

        parser = DemoParser(path)
        players = parser.parse_player_info()

        await ctx.send(f"Current url: {demo_url}\nDemo info:\n```{players}```")



async def setup(bot):
    await bot.add_cog(WatchDemoCog(bot))
