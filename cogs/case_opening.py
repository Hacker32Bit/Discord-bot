from time import sleep
import discord
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from discord.ext import commands
from dotenv import load_dotenv
from typing import Final
import os
import requests
import json

load_dotenv()
EVENTS_CHANNEL_ID: Final[str] = os.getenv("EVENTS_CHANNEL_ID")


class CaseOpening(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Case Opening\" cog is ready!")

    # Command for open case event
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def open_cs_case(self, ctx: discord.ext.commands.context.Context, user_id: str, case_name: str,
                           drop_url: str) -> None:

        try:
            r = requests.get(drop_url + '?l=english')
            while r.status_code == 429:
                print("Page is not loaded! Retrying after 10 seconds...")
                sleep(10)
                r = requests.get(drop_url + '?l=english')

            json_string = r.text.split('var g_rgAssets = ')[1].split('var g_rgCurrency')[0].strip().replace(';', '')

            data = json.loads(json_string)
            try:
                for _ in range(3):
                    data = data[next(iter(data))]
            except Exception as err:
                print(err)
                try:
                    data = data[0][0]
                except Exception as err2:
                    print(err2)

            name = data["name"]
            quality = data["descriptions"][0]["value"].split("Exterior:")[1].strip()
            rarity = data["type"]
            image_url = "https://community.fastly.steamstatic.com/economy/image/" + data["icon_url"]
            is_stattrak = "StatTrak" in rarity
            rarity = rarity.lower()
            if is_stattrak:
                rarity = rarity.replace('StatTrak™ ', '')
            if any(text.lower() in rarity for text in ["knife", "gloves", "extraordinary", "contraband", "★"]):
                rarity = "contraband"


        except Exception as err:
            print(err)
            return

        user = await self.client.fetch_user(user_id)

        print("user type", type(user))
        print("user", user)

        channel = await self.client.fetch_channel(1241019624313851969)
        print("user_id: ", user_id)
        print("drop_url: ", drop_url)
        print("case_name: ", case_name)
        print("name: ", name)
        print("quality: ", quality)
        print("rarity: ", rarity)
        print("is_stattrak: ", is_stattrak)
        result = "" + case_name + "\n" + name + "\n" + quality + "\n" + rarity + "\n" + str(is_stattrak)
        await channel.send(content=result)

    @staticmethod
    async def create_image(client, case_name: str, quality: str, drop_name: str, rarity: str):
        width = 800
        height = 600

        with Image.open(f"assets/images/cases/backgrounds/{rarity}.png") as image:
            notosans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                         'NotoSans-Bold.ttf')  # NOQA
            notosans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                            'NotoSans-Regular.ttf')  # NOQA
            rockybilly = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                      'Rockybilly.ttf')  # NOQA

            # ======== Fonts to use =============
            font_normal_large = truetype(notosans_bold, 36, encoding='UTF-8')
            font_normal = truetype(notosans_bold, 24, encoding='UTF-8')
            font_small_large = truetype(notosans_regular, 36, encoding='UTF-8')
            font_small = truetype(notosans_regular, 24, encoding='UTF-8')
            font_signa = truetype(rockybilly, 25, encoding='UTF-8')

            h_pos = 0
            new_height = 40

            white = (255, 255, 255, 255)
            black = (0, 0, 0, 255)

            gray_dark = (120, 144, 156, 255)
            gray = (144, 164, 174, 255)

            gray_dark_transparent = (120, 144, 156, 191)
            gray_transparent = (144, 164, 174, 191)

            draw = Draw(image)

            draw.rectangle([(0, h_pos), (width, new_height)], fill=gray_dark_transparent)
            draw.text((15, 2), "№", white, font=font_normal)
            draw.text((69, 2), "PARTICIPANT", white, font=font_normal)
            draw.text((width - 55, 2), "XP", white, font=font_normal)
            draw.line([(0, new_height - 2), (width, new_height - 2)], fill=gray_dark, width=2)

            image = image.crop((0, 0, width, new_height))
            return image


async def setup(client):
    await client.add_cog(CaseOpening(client))
