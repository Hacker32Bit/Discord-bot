from discord import app_commands
from discord.ext import commands
import discord
from demoparser2 import DemoParser
from dotenv import load_dotenv
from typing import Final
import os
import asyncio
from PIL import Image
from PIL.ImageFont import truetype
from PIL.ImageDraw import Draw
import requests
from discord import File
import io

load_dotenv()
STEAM_API_KEY: Final[str] = os.getenv("STEAM_API_KEY")
FACEIT_API_KEY: Final[str] = os.getenv("FACEIT_API_KEY")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")


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
            label=f"{profile['side']} {profile['name']}",
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
            f"{p['side']} {p['name']} — {p['steam_id']}"
            for p in view.profiles
            if view.state.get(p["steam_id"])
        ]

        if not selected:
            await interaction.response.send_message(
                "❌ No players selected.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "📤 Done!\n\n"
            "✅ Selected players:\n" + "\n".join(selected),
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


    @staticmethod
    async def create_image(self, profiles: list[dict], faceit_data):

        width = 800
        height = 600

        with Image.new(mode='RGBA', size=(width, height), color=(0, 0, 0, 0)) as image:
            font_noto_sans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                               'assets',
                                               'NotoSans-Bold.ttf')
            font_noto_sans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                                  'assets',
                                                  'NotoSans-Regular.ttf')
            # font_rockybilly= os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets', # NOQA: spellcheck
            #                           'Rockybilly.ttf') # NOQA: spellcheck

            # ======== Fonts to use =============
            font_normal_large = truetype(font_noto_sans_bold, 36, encoding='UTF-8')
            font_normal = truetype(font_noto_sans_bold, 24, encoding='UTF-8')
            font_small_large = truetype(font_noto_sans_regular, 36, encoding='UTF-8')
            font_small = truetype(font_noto_sans_regular, 24, encoding='UTF-8')
            # font_signa = truetype(font_rockybilly, 25, encoding='UTF-8') # NOQA: spellcheck

            h_pos = 0
            new_height = 40

            white = (255, 255, 255, 255)
            # black = (0, 0, 0, 255)

            gray_dark = (120, 144, 156, 255)
            gray = (144, 164, 174, 255)

            gray_dark_transparent = (120, 144, 156, 191)
            gray_transparent = (144, 164, 174, 191)

            draw = Draw(image)

            draw.rectangle([(0, h_pos), (width, new_height)], fill=gray_dark_transparent)
            draw.text((15, 2), f"{profiles[0]['name']}", white, font=font_normal)

            return image


    @app_commands.command(name="watch_demo", description="Analyze cs2 demo")
    async def watch_demo(self, interaction: discord.Interaction, demo_url: str = ""):
        log_channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)
        path = "/home/gektor/demo.dem"

        await interaction.response.defer()

        await interaction.edit_original_response(
            content="🔍 Searching demo..."
        )

        try:
            MATCH_ID = "1-e811c008-b088-45b5-929a-5f7035d2e1f7"

            headers = {
                "Authorization": f"Bearer {FACEIT_API_KEY}"
            }

            r = requests.get(
                f"https://open.faceit.com/data/v4/matches/{MATCH_ID}",
                headers=headers
            )
            r.raise_for_status()

            match = r.json()
            demo_urls = match["demo_url"]  # or "demos"
            teams = match["teams"]

            profiles = []
            for p in teams['faction1']['roster']:
                profiles.append({"name": p["nickname"], "steam_id": p["game_player_id"], "side": "[T]"})
            for p in teams['faction2']['roster']:
                profiles.append({"name": p["nickname"], "steam_id": p["game_player_id"], "side": "[CT]"})

            await interaction.edit_original_response(
                content="💾 Downloading demo..."
            )
            await asyncio.sleep(5)

            await interaction.edit_original_response(
                content="🕵️ Analyzing demo..."
            )

            parser = DemoParser(path)
            df = parser.parse_player_info()

            # build lookup: steamid -> df_index + 2
            index_map = {
                str(steamid): idx + 2
                for idx, steamid in df["steamid"].items()
            }

            profiles = [
                {
                    "index": index_map.get(p["steam_id"]),
                    **p
                }
                for p in profiles
            ]

            with io.BytesIO() as image_binary:
                image = await self.create_image(self, profiles=profiles, faceit_data=match)
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                result = File(fp=image_binary, filename="match.png")
                await interaction.edit_original_response(f"Current url: {demo_url}\nDemo info:\n```{profiles}```", attachments=[result])

            # Show profiles with checkbox buttons
            view = ProfileToggleView(interaction.author, profiles)

            await interaction.send(
                "Select Steam profiles:",
                view=view
            )

        except requests.exceptions.HTTPError as e:
            await log_channel.send(content=f"FaceIt connection error: {e}")





async def setup(bot):
    await bot.add_cog(WatchDemoCog(bot))
