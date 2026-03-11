from collections import defaultdict
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
from pathlib import Path
from urllib.parse import urlparse
import subprocess
import shutil
import re
from curl_cffi import requests as curl_requests

load_dotenv()
STEAM_API_KEY: Final[str] = os.getenv("STEAM_API_KEY")
FACEIT_API_KEY: Final[str] = os.getenv("FACEIT_API_KEY")
TINYURL_API_KEY: Final[str] = os.getenv("TINYURL_API_KEY")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")
GUILD_ID: Final[str] = os.getenv("GUILD_ID")
RAM_DIR = Path("/mnt/ramdisk")


class ProfileToggleView(discord.ui.View):
    def __init__(self, cog, author: discord.User, profiles: list[dict], download_url: str):
        super().__init__(timeout=60)
        self.cog = cog
        self.author = author
        self.profiles = profiles
        self.message: discord.Message | None = None
        self.download_url = download_url

        self.state = {p["steam_id"]: False for p in profiles}

        for index, profile in enumerate(profiles):
            self.add_item(ProfileToggleButton(profile, index))

        self.add_item(DoneButton())

    async def on_timeout(self):
        await self.process_done(None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ This interaction is not for you.",
                ephemeral=True
            )
            return False
        return True

    async def process_done(self, interaction: discord.Interaction | None):
        if interaction is not None and self.is_finished():
            self.stop()
            if hasattr(self, "cog"):
                self.cog.active_views.discard(self)
            return

        if interaction is not None and not await self.interaction_check(interaction):
            self.stop()
            if hasattr(self, "cog"):
                self.cog.active_views.discard(self)
            return

        selected = [
            p["index"]
            for p in self.profiles
            if self.state.get(p["steam_id"])
        ]

        selected_text = [
            f"{p['side']} {p['name']} — {p['steam_id']}"
            for p in self.profiles
            if self.state.get(p["steam_id"])
        ]

        if not selected:
            if interaction:
                await interaction.response.send_message(
                    "❌ No players selected.",
                    ephemeral=True
                )

                await interaction.message.edit(view=self)
            else:
                if self.message:
                    await self.message.delete()

            self.stop()
            if hasattr(self, "cog"):
                self.cog.active_views.discard(self)

            return

        team1, team2 = await DoneButton.tv_listen_voice_indices(sorted(selected))

        final_text = "✅ Selected voices:"
        final_command = f"tv_listen_voice_indices {team1}; tv_listen_voice_indices_h {team1};"

        final_text += f"```{final_command}```"

        if team2 != -1:
            inverted_command = f"tv_listen_voice_indices {team2}; tv_listen_voice_indices_h {team2};"
            final_text += f"Inverted voices:```{inverted_command}```"

        for item in self.children:
            item.disabled = True

        run_game_url = f'steam://rungameid/730/-console +"playdemo replays/demo; {final_command}"'

        headers = {
            "Authorization": f"Bearer {TINYURL_API_KEY}"
        }

        payload = {
            "url": run_game_url,
            "alias": "",
            "description": "string"
        }

        try:
            r = await asyncio.to_thread(
                requests.post,
                "https://api.tinyurl.com/create",
                headers=headers,
                json=payload
            )

            r.raise_for_status()
            tinyurl_data = r.json()

            if interaction:
                await interaction.response.send_message(
                    "📤 Done!\n\n"
                    f"{final_text}\u200b",
                    ephemeral=True,
                    view=WatchDemoView(tinyurl_data["data"]["tiny_url"], self.download_url)
                )

                await interaction.message.edit(view=self)

            else:
                # Timeout case
                if not self.message:
                    return

                await self.message.delete()

                # await self.message.edit(view=self)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

        self.stop()
        if hasattr(self, "cog"):
            self.cog.active_views.discard(self)


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


class WatchDemoButton(discord.ui.Button):
    def __init__(self, url: str = ""):
        super().__init__(
            label="Watch demo!",
            style=discord.ButtonStyle.link,
            emoji="<:cs2logo:1239536122141605888>",
            url=url
        )


class DownloadDemoButton(discord.ui.Button):
    def __init__(self, url: str = ""):
        super().__init__(
            label="Download demo",
            style=discord.ButtonStyle.link,
            emoji="<:faceit:1479851119353008339>",
            url=url
        )


class WatchDemoView(discord.ui.View):
    def __init__(self, url: str, download_url: str):
        super().__init__(timeout=None)
        self.add_item(DownloadDemoButton(download_url))
        self.add_item(WatchDemoButton(url))


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
        view: ProfileToggleView = self.view
        await view.process_done(interaction)


class WatchDemoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.demoQueue_order = []
        self.active_views = set()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Watch Demo\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Watch Demo\" was unloaded!")

    @staticmethod
    async def get_half_score(data, team_id, attr):
        for team in data:
            if team.get("team_id") == team_id:
                value = team["team_stats"].get(attr)
                return int(value) if value is not None else None
        return None

    async def extract_team_stats_with_parties(self, match_data, party_data, stats_data):
        result = dict()

        result["winner"] = match_data.get("detailed_results")[0]["winner"]
        result["location"] = match_data.get("voting")["location"]["pick"][0]
        result["map"] = match_data.get("voting")["map"]["pick"][0]
        result["map_name"] = next(
            m["name"] for m in match_data.get("voting")["map"]["entities"] if m["class_name"] == result["map"])

        teams = match_data['teams']
        for team in teams:
            team_info = dict()

            team_info["id"] = teams.get(team)["faction_id"]
            team_info["leader"] = teams.get(team)["leader"]
            team_info["name"] = teams.get(team)["name"]
            team_info["avatar"] = teams.get(team)["avatar"]
            team_info["average_lvl"] = teams.get(team)["stats"]["skillLevel"]["average"]
            team_info["team_elo"] = teams.get(team)["stats"]["rating"]
            team_info["score"] = match_data["results"]["score"].get(team)
            team_info["firstHalfScore"] = await self.get_half_score(stats_data["rounds"][0]["teams"],
                                                                    team_info.get("id"),
                                                                    "First Half Score")
            team_info["secondHalfScore"] = await self.get_half_score(stats_data["rounds"][0]["teams"],
                                                                     team_info.get("id"),
                                                                     "Second Half Score")

            result[team] = team_info

        # playerId -> partyId
        player_party = {}
        for party in party_data["payload"]["parties"]:
            for user in party["users"]:
                player_party[user] = party["partyId"]

        team_to_faction = {
            result["faction1"]["id"]: "faction1",
            result["faction2"]["id"]: "faction2"
        }

        # create parties structure
        for faction in ["faction1", "faction2"]:
            result[faction]["parties"] = defaultdict(list)

        for team in stats_data["rounds"][0]["teams"]:
            team_id = team["team_id"]

            if team_id not in team_to_faction:
                continue

            faction = team_to_faction[team_id]

            for player in team["players"]:
                pid = player["player_id"]
                party_id = player_party.get(pid, pid)  # solo fallback
                elo = next(p["elo"] for p in party_data["payload"]["teams"].get(faction)["roster"] if p["id"] == pid)
                gameSkillLevel = next(
                    p["gameSkillLevel"] for p in party_data["payload"]["teams"].get(faction)["roster"] if
                    p["id"] == pid)

                result[faction]["parties"][party_id].append({
                    "playerId": pid,
                    "nickname": player.get("nickname"),
                    "elo": elo,
                    "gameSkillLevel": gameSkillLevel,
                    "kills": player["player_stats"].get("Kills"),
                    "deaths": player["player_stats"].get("Deaths"),
                    "assists": player["player_stats"].get("Assists"),
                    "adr": player["player_stats"].get("ADR"),
                    "kd": player["player_stats"].get("K/D Ratio"),
                    "kr": player["player_stats"].get("K/R Ratio"),
                    "headshots": player["player_stats"].get("Headshots"),  # hs% = hs / kills * 100
                    "5k": player["player_stats"].get("Penta Kills"),
                    "4k": player["player_stats"].get("Quadro Kills"),
                    "3k": player["player_stats"].get("Triple Kills"),
                    "2k": player["player_stats"].get("Double Kills"),
                    "mvps": player["player_stats"].get("MVPs"),
                })

        # convert to sorted list
        for faction in ["faction1", "faction2"]:
            parties = []

            for party_id, players in result[faction]["parties"].items():
                parties.append({
                    "partyId": party_id,
                    "size": len(players),
                    "players": players
                })

            # sort by party size (largest first)
            parties.sort(key=lambda p: p["size"], reverse=True)

            result[faction]["parties"] = parties

        return result

    async def update_player(self, player):
        headers = {
            "Authorization": f"Bearer {FACEIT_API_KEY}"
        }

        player_id = player["playerId"]

        r = requests.get(
            f"https://open.faceit.com/data/v4/players/{player_id}",
            headers=headers
        )
        r.raise_for_status()
        p = r.json()

        # add new fields
        player["avatar"] = p.get("avatar")
        if player["avatar"] != '':
            player["avatar_platform"] = "faceit"
        else:
            player["avatar_platform"] = "steam"

        player["country"] = p.get("country")
        player["cover_image"] = p.get("cover_image")

        player["steam_id_64"] = p.get("steam_id_64")
        player["memberships"] = p.get("memberships", [])
        player["membership_type"] = p.get("membership_type")
        player["cover_featured_image"] = p.get("cover_featured_image")
        player["verified"] = p.get("verified")

        # game stats
        cs2 = p.get("games", {}).get("cs2", {})
        player["actual_skill_level"] = cs2.get("skill_level")
        player["actual_faceit_elo"] = cs2.get("faceit_elo")

    # Command for test new version of /watch_demo
    @commands.command(help="watch_demo2", description="Command for test new version of /watch_demo")
    @commands.has_any_role("Owner", "Admin")
    async def watch_demo2(self, ctx):
        log_channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)
        MATCH_ID = "1-66cd0f2a-8991-4555-b824-1c5bd047d011"

        headers = {
            "Authorization": f"Bearer {FACEIT_API_KEY}"
        }
        r = await asyncio.to_thread(
            requests.get,
            f"https://open.faceit.com/data/v4/matches/{MATCH_ID}",
            headers=headers
        )
        r.raise_for_status()
        match_data = r.json()
        # print(match_data)

        r = await asyncio.to_thread(
            requests.get,
            f"https://open.faceit.com/data/v4/matches/{MATCH_ID}/stats",
            headers=headers
        )
        r.raise_for_status()
        stats_data = r.json()
        # print(stats_data)

        r = await asyncio.to_thread(
            curl_requests.get,
            f"https://www.faceit.com/api/match/v2/match/{MATCH_ID}",
            impersonate="chrome"
        )
        party_data = r.json()
        # print(party_data)

        data = await self.extract_team_stats_with_parties(match_data, party_data, stats_data)

        # iterate factions
        for faction in ["faction1", "faction2"]:
            for party in data[faction]["parties"]:
                for player in party["players"]:
                    await self.update_player(player)

        players = []
        steam_ids = []

        for faction in ["faction1", "faction2"]:
            for party in data[faction]["parties"]:
                for player in party["players"]:
                    players.append(player)

                    sid = player.get("steam_id_64")
                    if sid:
                        steam_ids.append(sid)

        steam_ids = list(set(steam_ids))

        try:
            steamids = ",".join(steam_ids)
            url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamids}"

            r = await asyncio.to_thread(requests.get, url)

            while r.status_code == 429:
                sleep_time = randint(1800, 3600)
                await log_channel.send(
                    content=f"Steam error 429. Too many request. Sleeping {sleep_time // 60} minutes before retrying.")
                await asyncio.sleep(sleep_time)
                r = await asyncio.to_thread(requests.get, url)

            r.raise_for_status()
            steam_data = r.json()

            steam_lookup = {}

            for p in steam_data["response"]["players"]:
                avatar = (
                        p.get("avatarfull")
                        or p.get("avatarmedium")
                        or p.get("avatar")
                        or None
                )

                steam_lookup[p["steamid"]] = avatar

            for faction in ["faction1", "faction2"]:
                for party in data[faction]["parties"]:
                    for player in party["players"]:
                        sid = player.get("steam_id_64")
                        player["steam_avatar"] = steam_lookup.get(sid)
        except Exception as e:
            print(e)

        with io.BytesIO() as image_binary:
            image = await self.create_image_new(data=data)
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            result = File(fp=image_binary, filename="match.png")
            await ctx.send(file=result)

    @staticmethod
    def create_avatar(avatar: Image.Image) -> Image.Image:
        INPUT_SIZE = 120
        FINAL_SIZE = 40
        SCALE = 3
        PADDING = 1

        avatar = avatar.convert("RGBA").resize((INPUT_SIZE, INPUT_SIZE), Image.LANCZOS)

        canvas_size = INPUT_SIZE + PADDING * 2

        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        canvas.paste(avatar, (PADDING, PADDING))

        # smooth circle mask
        mask = Image.new("L", (canvas_size * SCALE, canvas_size * SCALE), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, canvas_size * SCALE, canvas_size * SCALE), fill=255)

        mask = mask.resize((canvas_size, canvas_size), Image.LANCZOS)

        canvas.putalpha(mask)

        # downscale to final avatar
        avatar_final = canvas.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)

        return avatar_final

    @staticmethod
    def draw_smooth_corner(draw, x, y, color, length_v=25, length_h=9, radius=8, width=2, kind="up_right"):
        """
        Draw a smooth corner.

        kind options:
            - "up_right"   ┌
            - "middle_right"  |-
            - "down_right" └
        """
        if kind == "up_right":
            # vertical line down
            draw.line((x, y + radius - width - 1, x, y + length_v), fill=color, width=width)
            # horizontal line right
            draw.line((x + radius - width - 1, y, x + length_h, y), fill=color, width=width)
            # corner
            draw.arc((x, y, x + radius, y + radius), start=180, end=270, fill=color, width=width)

        elif kind == "middle_right":
            # simple vertical then horizontal (no arc)
            draw.line((x, y - length_v, x, y + length_v), fill=color, width=width)
            draw.line((x, y, x + length_h, y), fill=color, width=width)

        elif kind == "down_right":
            # vertical line down
            draw.line((x, y - length_v, x, y - radius + width + 1), fill=color, width=width)
            # horizontal line right
            draw.line((x + radius - width - 1, y, x + length_h, y), fill=color, width=width)
            # corner
            draw.arc((x, y - radius, x + radius, y), start=90, end=180, fill=color, width=width)

    async def create_image_new(self, data):
        width = 800
        height = 600

        with Image.open(f"assets/images/cs2maps/{data.get('map')}_template.png").convert("RGBA") as image:
            font_noto_sans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                               'assets',
                                               'NotoSans-Bold.ttf')
            font_noto_sans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                                  'assets',
                                                  'NotoSans-Regular.ttf')
            # font_rockybilly= os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets', # NOQA: spellcheck
            #                           'Rockybilly.ttf') # NOQA: spellcheck

            # ======== Fonts to use =============
            font_normal_large = truetype(font_noto_sans_bold, 24, encoding='UTF-8')
            font_normal = truetype(font_noto_sans_bold, 14, encoding='UTF-8')
            font_small_large = truetype(font_noto_sans_regular, 14, encoding='UTF-8')
            font_small = truetype(font_noto_sans_regular, 13, encoding='UTF-8')
            # font_signa = truetype(font_rockybilly, 25, encoding='UTF-8') # NOQA: spellcheck

            #####################################
            ### Draw main information
            #####################################
            h_pos = 300
            w_pos = 25

            white = (255, 255, 255, 255)
            faceit_color = (255, 85, 0, 255)
            # black = (0, 0, 0, 255)

            draw = Draw(image)

            # Draw faction1 score
            draw.text((w_pos, h_pos), str(data["faction1"]["score"]),
                      fill=(faceit_color if data["winner"] == "faction1" else white), font=font_normal_large,
                      anchor="mm", align="center")
            draw.text((width - w_pos, h_pos), str(data["faction2"]["score"]),
                      fill=(faceit_color if data["winner"] == "faction2" else white), font=font_normal_large,
                      anchor="mm", align="center")

            # Draw map name
            w_pos = 400
            draw.text((w_pos, h_pos), data["map_name"], fill=white, font=font_normal_large, anchor="mm", align="center")

            #####################################
            ### Draw teams images
            #####################################
            # Draw faction1 avatar
            # Fetch images
            w_pos = 48
            h_pos = 280
            if data["faction1"]["avatar"]:
                try:
                    response = await asyncio.to_thread(requests.get, data["faction1"]["avatar"])
                    response.raise_for_status()
                except Exception as e:
                    avatar = Image.open("assets/images/undefined_faceit_avatar.png").convert("RGBA")

                if response.status_code == 200:
                    avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
            else:
                avatar = Image.open("assets/images/undefined_faceit_avatar.png").convert("RGBA")

            circle_avatar = self.create_avatar(avatar)
            image.paste(circle_avatar, (w_pos, h_pos), circle_avatar)

            ### For faction2
            if data["faction2"]["avatar"]:
                try:
                    response = await asyncio.to_thread(requests.get, data["faction2"]["avatar"])
                    response.raise_for_status()
                except Exception as e:
                    avatar = Image.open("assets/images/undefined_faceit_avatar.png").convert("RGBA")

                if response.status_code == 200:
                    avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
            else:
                avatar = Image.open("assets/images/undefined_faceit_avatar.png").convert("RGBA")

            circle_avatar = self.create_avatar(avatar)
            image.paste(circle_avatar, (width - w_pos - 40, h_pos), circle_avatar)

            #####################################
            ### Draw teams names, avg elo, and elo icon
            #####################################
            # For faction1
            w_pos = 95
            h_pos = 295
            draw.text((w_pos, h_pos), data["faction1"]["name"], fill=white, font=font_normal, anchor="ls", align="left")
            draw.text((w_pos + 25, h_pos + 20), "{:,}".format(data["faction1"]["team_elo"]), fill=white,
                      font=font_small, anchor="ls",
                      align="left")

            faceit_lvl = Image.open(f"assets/images/faceitlvls/lvl{data['faction1']['average_lvl']}.png").convert(
                "RGBA")
            faceit_lvl = faceit_lvl.resize((20, 20), Image.LANCZOS)
            image.paste(faceit_lvl, (w_pos, h_pos + 5), faceit_lvl)

            # For faction2
            draw.text((width - w_pos, h_pos), data["faction2"]["name"], fill=white, font=font_normal, anchor="rs",
                      align="right")
            draw.text((width - w_pos - 25, h_pos + 20), "{:,}".format(data["faction2"]["team_elo"]), fill=white,
                      font=font_small, anchor="rs",
                      align="right")

            faceit_lvl = Image.open(f"assets/images/faceitlvls/lvl{data['faction2']['average_lvl']}.png").convert(
                "RGBA")
            faceit_lvl = faceit_lvl.resize((20, 20), Image.LANCZOS)
            image.paste(faceit_lvl, (width - w_pos - 20, h_pos + 5), faceit_lvl)

            #####################################
            ### Draw players stats
            #####################################
            # For faction1
            w_pos = 10
            h_pos = 50
            for party in data["faction1"]["parties"]:
                if party["size"] == 1:
                    draw.rectangle([(w_pos - 2, h_pos - 2), (w_pos + 2, h_pos + 2)], fill=faceit_color)

                for index, player in enumerate(party["players"]):
                    # Draw teammates lines
                    if party["size"] > 1 and index == 0:
                        self.draw_smooth_corner(draw, w_pos, h_pos, faceit_color, kind="up_right")
                    elif party["size"] > 1 and index != party["size"] - 1:
                        self.draw_smooth_corner(draw, w_pos, h_pos, faceit_color, kind="middle_right")
                    elif party["size"] > 1 and index == party["size"] - 1:
                        self.draw_smooth_corner(draw, w_pos, h_pos, faceit_color, kind="down_right")
                    h_pos += 50
                    # Draw stats

            return image

    @staticmethod
    async def fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width=138,
                       ellipsis="...") -> str:
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

            t_color = (251, 172, 24, 255)
            ct_color = (40, 57, 127, 255)

            gray_transparent = (144, 164, 174, 191)

            draw = Draw(image)

            log_channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)

            # Draw T side players avatars
            for p in profiles[:5]:
                if p["faceit_avatar_url"]:
                    try:
                        response = await asyncio.to_thread(requests.get, p['faceit_avatar_url'])
                        response.raise_for_status()
                    except Exception as e:
                        try:
                            response = await asyncio.to_thread(requests.get, p['steam_avatar_url'])
                            response.raise_for_status()
                        except Exception as e:
                            await log_channel.send("FaceIt + Steam images not fetched!")
                else:
                    try:
                        response = await asyncio.to_thread(requests.get, p['steam_avatar_url'])
                        response.raise_for_status()
                    except Exception as e:
                        await log_channel.send("Steam images not fetched!")

                if response.status_code == 200:
                    avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
                else:
                    avatar = Image.open("assets/images/undefined_steam_avatar.jpg").convert("RGBA")

                avatar = avatar.resize((158, 158), Image.LANCZOS)

                image.paste(avatar, (w_pos, h_pos), avatar)

                if w_pos < 640:
                    w_pos = w_pos + 158
                    draw.line([(w_pos, h_pos), (w_pos, h_pos + 158)], fill=gray_transparent, width=2)
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

            # Draw in one pass ( the best kerning)
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

            # Draw CT side players avatars
            for p in profiles[5:]:
                if p["faceit_avatar_url"]:
                    try:
                        response = await asyncio.to_thread(requests.get, p['faceit_avatar_url'])
                        response.raise_for_status()
                    except Exception as e:
                        try:
                            response = await asyncio.to_thread(requests.get, p['steam_avatar_url'])
                            response.raise_for_status()
                        except Exception as e:
                            await log_channel.send("FaceIt + Steam images not fetched!")
                else:
                    try:
                        response = await asyncio.to_thread(requests.get, p['steam_avatar_url'])
                        response.raise_for_status()
                    except Exception as e:
                        await log_channel.send("Steam images not fetched!")

                if response.status_code == 200:
                    avatar = Image.open(io.BytesIO(response.content)).convert("RGBA")
                else:
                    avatar = Image.open("assets/images/undefined_steam_avatar.jpg").convert("RGBA")

                avatar = avatar.resize((158, 158), Image.LANCZOS)

                image.paste(avatar, (w_pos, h_pos), avatar)

                if w_pos < 640:
                    w_pos = w_pos + 158
                    draw.line([(w_pos, h_pos), (w_pos, h_pos + 158)], fill=gray_transparent, width=2)
                    w_pos = w_pos + 2

            return image

    async def download_demo(self, url, interaction, log_channel):
        output_path = RAM_DIR / f"{interaction.id}.dem.zst"

        def _download():
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

        try:
            await asyncio.to_thread(_download)
        except Exception as e:
            await log_channel.send(f"Download error: {e}")
            if output_path.exists():
                output_path.unlink()
            if interaction.id in self.demoQueue_order:
                self.demoQueue_order.remove(interaction.id)
            return 1

        return 0

    async def wait_for_memory_space(self, interaction, log_channel, check_every=15):
        position = None  # Will calculate dynamically

        while True:
            try:
                total, used, free = shutil.disk_usage("/mnt/ramdisk")
            except OSError as e:
                await log_channel.send(content=f"disk_usageError: {e}")
                return 1

            try:
                position = self.demoQueue_order.index(interaction.id)
            except ValueError:
                await log_channel.send(
                    content=f"ValueError: demoQueue_order {interaction.id} - {interaction.user.name}"
                )
                return 1

            final_response = ""

            if free >= 2 * 1024 ** 3:
                if position < 1:
                    return 0
                else:
                    final_response = f"⏳ [{position}] You are in queue... Please wait..."
            else:
                final_response = f"📟 Not enough RAM disk space.\n⏳ [{position}] You are in queue... Please wait..."

            try:
                await interaction.edit_original_response(
                    content=final_response
                )
            except Exception as e:  # catch discord exceptions
                await log_channel.send(content=f"editResponseError: {e}")
                return 1

            await asyncio.sleep(check_every)

    @app_commands.command(name="watch_demo", description="Analyze cs2 demo")
    async def watch_demo(self, interaction: discord.Interaction, demo_url_or_id: str = ""):
        await interaction.response.defer()
        log_channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)

        demo_id = None
        is_faceit = False
        is_link = False
        demo_url = None

        demo_url_or_id = demo_url_or_id.strip()

        # Regex for Faceit match ID (with optional prefix, e.g., "1-")
        faceit_id_pattern = re.compile(
            r"(?:\d-)?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

        # Check if input is a URL
        if demo_url_or_id.startswith("http://") or demo_url_or_id.startswith("https://"):
            is_link = True
            parsed = urlparse(demo_url_or_id)

            if "faceit.com" in parsed.netloc.lower():
                is_faceit = True

            # Extract match ID from URL path
            match = faceit_id_pattern.search(parsed.path)
            if match:
                demo_id = match.group(0)

        else:
            # Assume raw ID
            if faceit_id_pattern.fullmatch(demo_url_or_id):
                demo_id = demo_url_or_id
                is_faceit = True
            else:
                await interaction.response.send_message("❌ Invalid URL or Faceit match ID.")
                return

        # Build full Faceit demo URL
        if demo_id and is_faceit:
            demo_url = f"https://www.faceit.com/en/cs2/room/{demo_id}/scoreboard"

        await interaction.edit_original_response(
            content="🔍 Searching demo..."
        )

        try:
            headers = {
                "Authorization": f"Bearer {FACEIT_API_KEY}"
            }

            r = await asyncio.to_thread(
                requests.get,
                f"https://open.faceit.com/data/v4/matches/{demo_id}",
                headers=headers,
            )

            r.raise_for_status()

            faceit_data = r.json()
            demo_urls = faceit_data["demo_url"][0]  # or "demos"
            teams = faceit_data["teams"]

            game_player_ids = [
                player["game_player_id"]
                for faction in ("faction1", "faction2")
                for player in teams[faction]["roster"]
            ]

            try:
                steamids = ",".join(game_player_ids)
                url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steamids}"

                r = await asyncio.to_thread(requests.get, url)

                while r.status_code == 429:
                    sleep_time = randint(1800, 3600)
                    await log_channel.send(
                        content=f"Steam error 429. Too many request. Sleeping {sleep_time // 60} minutes before retrying.")
                    await asyncio.sleep(sleep_time)
                    r = await asyncio.to_thread(requests.get, url)

                r.raise_for_status()
                steam_data = r.json()

                players = steam_data["response"]["players"]
                steam_index = {p["steamid"]: p for p in players}

                profiles = []
                for p in teams['faction1']['roster']:
                    faceit_avatar_url = p["avatar"]
                    steam_avatar_url = steam_index[p["game_player_id"]]["avatarfull"]
                    profiles.append({"name": p["nickname"], "steam_id": p["game_player_id"], "side": "[T]",
                                     "faceit_avatar_url": faceit_avatar_url, "steam_avatar_url": steam_avatar_url})
                for p in teams['faction2']['roster']:
                    faceit_avatar_url = p["avatar"]
                    steam_avatar_url = steam_index[p["game_player_id"]]["avatarfull"]
                    profiles.append({"name": p["nickname"], "steam_id": p["game_player_id"], "side": "[CT]",
                                     "faceit_avatar_url": faceit_avatar_url, "steam_avatar_url": steam_avatar_url})

                interaction_id = interaction.id

                self.demoQueue_order.append(interaction_id)

                await interaction.edit_original_response(
                    content=f"⏳ You are in queue..."
                )

                status = await self.wait_for_memory_space(interaction, log_channel)
                if status == 1:
                    return

                await interaction.edit_original_response(
                    content="💾 Downloading demo..."
                )

                r = await asyncio.to_thread(
                    requests.post,
                    f"https://open.faceit.com/download/v2/demos/download",
                    headers=headers,
                    json={
                        "resource_url": demo_urls,
                    },
                )
                r.raise_for_status()

                data = r.json()
                resource_url = data["payload"]["download_url"]

                status = await self.download_demo(resource_url, interaction, log_channel)

                if status == 1:
                    return

                await interaction.edit_original_response(
                    content="💾️ Extracting demo..."
                )

                zst_path = RAM_DIR / f"{interaction_id}.dem.zst"
                dem_path = RAM_DIR / f"{interaction_id}.dem"

                try:
                    await asyncio.to_thread(
                        subprocess.run,
                        ["zstd", "-d", "--rm", zst_path, "-o", dem_path],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    # Only remove files if they exist
                    if zst_path.exists():
                        zst_path.unlink()
                    if dem_path.exists():
                        dem_path.unlink()
                    if interaction.id in self.demoQueue_order:
                        self.demoQueue_order.remove(interaction.id)
                    await log_channel.send(content=f"subprocessError: {e}")
                    await interaction.edit_original_response(
                        content=f"⚠️️ [ERROR] Something went wrong :(. Please tell admin about it!\nInteraction ID: {interaction.id}"
                    )
                    return

                await interaction.edit_original_response(
                    content="🕵️ Analyzing demo..."
                )

                try:
                    def parse_demo():
                        parser = DemoParser(dem_path.absolute().as_posix())
                        return parser.parse_player_info()

                    df = await asyncio.to_thread(parse_demo)
                except Exception as e:
                    if dem_path.exists():
                        dem_path.unlink()
                    if interaction.id in self.demoQueue_order:
                        self.demoQueue_order.remove(interaction.id)
                    await log_channel.send(content=f"DemoParserError: {e}")
                    return

                if dem_path.exists():
                    dem_path.unlink()
                if interaction.id in self.demoQueue_order:
                    self.demoQueue_order.remove(interaction.id)

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

                view = ProfileToggleView(self, interaction.user, profiles, resource_url)
                self.active_views.add(view)

                with io.BytesIO() as image_binary:
                    image = await self.create_image(profiles=profiles, faceit_data=faceit_data)
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    result = File(fp=image_binary, filename="match.png")
                    msg = await interaction.edit_original_response(
                        content=f"Your match: <{demo_url}>\n",
                        attachments=[result],
                        view=view
                    )

                    view.message = msg

            except requests.exceptions.HTTPError as e:
                await log_channel.send(content=f"Steam connection error: {e}")


        except requests.exceptions.HTTPError as e:
            await log_channel.send(content=f"FaceIt connection error: {e}")


async def setup(bot):
    await bot.add_cog(WatchDemoCog(bot), guilds=[discord.Object(id=GUILD_ID)])
