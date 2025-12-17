from random import randint
from discord import app_commands
from discord.ext import commands
import discord
from demoparser2 import DemoParser
from dotenv import load_dotenv
from typing import Final
import os
import asyncio
from PIL import Image, ImageOps, ImageDraw, ImageFont
from PIL.ImageFont import truetype
from PIL.ImageDraw import Draw
import requests
from discord import File
import io


load_dotenv()
STEAM_API_KEY: Final[str] = os.getenv("STEAM_API_KEY")
FACEIT_API_KEY: Final[str] = os.getenv("FACEIT_API_KEY")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")


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

    @staticmethod
    async def tv_listen_voice_indices(array):
            if len(array) == 10:
                return -1, -1

            def tv_listen_value(players):
                """
                Convert player indices (1-based) into decimal tv_listen_voice_indices value.
                Example: [2, 3, 5, 8, 10] -> 662
                """
                return sum(1 << (p - 1) for p in players)

            players1 = list(map(int, array))
            # All numbers from 2 to 11 (inclusive), excluding players1
            players2 = [p for p in range(2, 12) if p not in players1]
            result1 = tv_listen_value(players1)
            result2 = tv_listen_value(players2)
            return result1, result2

    async def callback(self, interaction: discord.Interaction):
        view: ProfileToggleView = self.view  # type: ignore

        selected = [
            p["index"]
            for p in view.profiles
            if view.state.get(p["steam_id"])
        ]

        selected_text = [
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

        team1, team2 = await self.tv_listen_voice_indices(sorted(selected))
        final_command = ""
        if team1 == -1:
            final_command = f"✅ Selected voices:\n```tv_listen_voice_indices {team1}; tv_listen_voice_indices_h {team1};```"
        else:
            final_command = f"✅ Selected voices:\n```tv_listen_voice_indices {team1}; tv_listen_voice_indices_h {team1};```\nInverted voices:\n```tv_listen_voice_indices {team2}; tv_listen_voice_indices_h {team2};```"

        await interaction.response.send_message(
            "📤 Done!\n\n"
            "✅ Selected players:\n" + "\n".join(selected_text) + f"\n{final_command}",
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
    async def fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width = 138, ellipsis = "...") -> str:
        # If full text fits — return as is
        if draw.textlength(text, font=font) <= max_width:
            return text

        ellipsis_width = draw.textlength(ellipsis, font=font)

        # Trim text until it fits with ellipsis
        for i in range(len(text), 0, -1):
            candidate = text[:i]
            if draw.textlength(candidate, font=font) + ellipsis_width <= max_width:
                return candidate + ellipsis

        return ellipsis


    @staticmethod
    async def create_image(self, profiles: list[dict], faceit_data):

        width = 798
        height = 436

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
            font_normal_large = truetype(font_noto_sans_bold, 38, encoding='UTF-8')
            font_normal = truetype(font_noto_sans_bold, 18, encoding='UTF-8')
            font_small_large = truetype(font_noto_sans_regular, 28, encoding='UTF-8')
            font_small = truetype(font_noto_sans_regular, 18, encoding='UTF-8')
            # font_signa = truetype(font_rockybilly, 25, encoding='UTF-8') # NOQA: spellcheck

            h_pos = 0
            w_pos = 0

            white = (255, 255, 255, 255)
            # black = (0, 0, 0, 255)

            gray_dark = (120, 144, 156, 255)
            gray = (144, 164, 174, 255)

            t_color = (245, 127, 23, 255)
            ct_color = (26, 35, 126, 255)

            gray_dark_transparent = (120, 144, 156, 191)
            gray_transparent = (144, 164, 174, 191)

            draw = Draw(image)

            # draw.text((15, 2), f"{profiles[0]['name']}", white, font=font_normal)

            log_channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)

            # Draw T side players avatars
            for p in profiles[:5]:
                if p["faceit_avatar_url"]:
                    try:
                        response = requests.get(p['faceit_avatar_url'])
                        response.raise_for_status()
                    except Exception as e:
                        try:
                            response = requests.get(p['steam_avatar_url'])
                        except Exception as e:
                            await log_channel.send("FaceIt + Steam images not fetched!")
                else:
                    try:
                        response = requests.get(p['steam_avatar_url'])
                    except Exception as e:
                        await log_channel.send("Steam images not fetched!")

                avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
                avatar = avatar.resize((158, 158), Image.LANCZOS)

                image.paste(avatar, (w_pos, 0), avatar)

                if w_pos < 640:
                    w_pos = w_pos + 158
                    draw.line([(w_pos, 0), (w_pos, 158)], fill=gray_transparent, width=2)
                    w_pos = w_pos + 2

            w_pos = 0
            h_pos = 158

            draw.line([(0, h_pos), (width, h_pos)], fill=gray_transparent, width=2)
            h_pos = h_pos + 2

            # Draw T side players nicknames
            for p in profiles[:5]:
                draw.rectangle([(w_pos, h_pos), (width, h_pos + 26)], fill=t_color)

                text = p["name"]
                fitted = await self.fit_text(draw, text, font_small)

                draw.text((w_pos + 7, h_pos - 1), fitted, fill=white, font=font_small)

                if w_pos < 640:
                    w_pos = w_pos + 158
                    draw.line([(w_pos, h_pos), (w_pos, h_pos + 26)], fill=gray_transparent, width=2)
                    w_pos = w_pos + 2

            w_pos = 0
            h_pos = h_pos + 26
            draw.line([(0, h_pos), (width, h_pos)], fill=gray_transparent, width=2)
            h_pos = h_pos + 2

            # Paste gradient
            background = Image.open("assets/images/watch_demo_gradient.png").convert("RGBA")
            image.paste(background, (w_pos, h_pos), background)

            text = faceit_data["teams"]["faction1"]["name"]
            fitted = await self.fit_text(draw, text, font_small_large, max_width=320)
            draw.text((w_pos + 10, h_pos + 10), fitted, fill=white, font=font_small_large)

            text = faceit_data["teams"]["faction2"]["name"]
            fitted = await self.fit_text(draw, text, font_small_large, max_width=320)

            bbox = draw.textbbox((0, 0), fitted, font=font_small_large)
            text_width = bbox[2] - bbox[0]

            right_edge = width - 10  # where text should END

            draw.text(
                (right_edge - text_width, h_pos + 10),
                fitted,
                fill=white,
                font=font_small_large
            )

            score1 = str(faceit_data["results"]["score"]["faction1"])
            score2 = str(faceit_data["results"]["score"]["faction2"])

            left_text = f"{score1} "
            colon = ":"
            right_text = f" {score2}"

            # Measure widths
            left_bbox = draw.textbbox((0, 0), left_text, font=font_normal_large)
            colon_bbox = draw.textbbox((0, 0), colon, font=font_normal_large)

            left_w = left_bbox[2] - left_bbox[0]
            colon_w = colon_bbox[2] - colon_bbox[0]

            center_x = width // 2  # = 399

            # X where full string must start so COLON CENTER is at center_x
            start_x = center_x - left_w - colon_w // 2

            # Draw in one pass (best kerning)
            draw.text(
                (start_x, h_pos + 2),
                f"{left_text}{colon}{right_text}",
                fill=white,
                font=font_normal_large
            )

            w_pos = 0
            h_pos = h_pos + 60
            draw.line([(0, h_pos), (width, h_pos)], fill=gray_transparent, width=2)
            h_pos = h_pos + 2

            # Draw CT side players nicknames
            for p in profiles[5:]:
                draw.rectangle([(w_pos, h_pos), (width, h_pos + 26)], fill=ct_color)

                text = p["name"]
                fitted = await self.fit_text(draw, text, font_small)

                draw.text((w_pos + 7, h_pos - 1), fitted, fill=white, font=font_small)

                if w_pos < 640:
                    w_pos = w_pos + 158
                    draw.line([(w_pos, h_pos), (w_pos, h_pos + 26)], fill=gray_transparent, width=2)
                    w_pos = w_pos + 2

            w_pos = 0
            h_pos = h_pos + 26
            draw.line([(0, h_pos), (width, h_pos)], fill=gray_transparent, width=2)
            h_pos = h_pos + 2

            # Draw T side players avatars
            for p in profiles[5:]:
                if p["faceit_avatar_url"]:
                    try:
                        response = requests.get(p['faceit_avatar_url'])
                        response.raise_for_status()
                    except Exception as e:
                        try:
                            response = requests.get(p['steam_avatar_url'])
                        except Exception as e:
                            await log_channel.send("FaceIt + Steam images not fetched!")
                else:
                    try:
                        response = requests.get(p['steam_avatar_url'])
                    except Exception as e:
                        await log_channel.send("Steam images not fetched!")

                avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
                avatar = avatar.resize((158, 158), Image.LANCZOS)

                image.paste(avatar, (w_pos, h_pos), avatar)

                if w_pos < 640:
                    w_pos = w_pos + 158
                    draw.line([(w_pos, h_pos), (w_pos, h_pos + 158)], fill=gray_transparent, width=2)
                    w_pos = w_pos + 2

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
            MATCH_ID = "1-be283e06-85db-462e-a73b-ef31b3b52d6d"

            headers = {
                "Authorization": f"Bearer {FACEIT_API_KEY}"
            }

            r = requests.get(
                f"https://open.faceit.com/data/v4/matches/{MATCH_ID}",
                headers=headers
            )
            r.raise_for_status()

            faceit_data = r.json()
            demo_urls = faceit_data["demo_url"]  # or "demos"
            teams = faceit_data["teams"]

            game_player_ids = [
                player["game_player_id"]
                for faction in ("faction1", "faction2")
                for player in teams[faction]["roster"]
            ]

            try:
                steamids = ",".join(game_player_ids)
                url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamids}"

                r = requests.get(url)
                while r.status_code == 429:
                    sleep_time = randint(1800, 3600)
                    await log_channel.send(
                        content=f"Steam error 429. Too many request. Sleeping {sleep_time // 60} minutes before retrying.")
                    await asyncio.sleep(sleep_time)
                    r = requests.get(url)

                r.raise_for_status()
                steam_data = r.json()

                players = steam_data["response"]["players"]
                steam_index = {p["steamid"]: p for p in players}

                profiles = []
                for p in teams['faction1']['roster']:
                    faceit_avatar_url = p["avatar"]
                    steam_avatar_url = steam_index[p["game_player_id"]]["avatarfull"]
                    profiles.append({"name": p["nickname"], "steam_id": p["game_player_id"], "side": "[T]", "faceit_avatar_url": faceit_avatar_url, "steam_avatar_url": steam_avatar_url})
                for p in teams['faction2']['roster']:
                    faceit_avatar_url = p["avatar"]
                    steam_avatar_url = steam_index[p["game_player_id"]]["avatarfull"]
                    profiles.append({"name": p["nickname"], "steam_id": p["game_player_id"], "side": "[CT]", "faceit_avatar_url": faceit_avatar_url, "steam_avatar_url": steam_avatar_url})

                await interaction.edit_original_response(
                    content="💾 Downloading demo..."
                )

                # TODO
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

                view = ProfileToggleView(interaction.user, profiles)

                with io.BytesIO() as image_binary:
                    image = await self.create_image(self, profiles=profiles, faceit_data=faceit_data)
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    result = File(fp=image_binary, filename="match.png")
                    await interaction.edit_original_response(
                        content=f"Current url: {demo_url}\n", attachments=[result],
                        view=view)


            except requests.exceptions.HTTPError as e:
                await log_channel.send(content=f"Steam connection error: {e}")



        except requests.exceptions.HTTPError as e:
            await log_channel.send(content=f"FaceIt connection error: {e}")



async def setup(bot):
    await bot.add_cog(WatchDemoCog(bot), guilds=[discord.Object(id=GUILD_ID)])
