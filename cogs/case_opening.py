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
import io
from discord import File

load_dotenv()
EVENTS_CHANNEL_ID: Final[str] = os.getenv("EVENTS_CHANNEL_ID")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")


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
            ansi_color = '[2;34m'
            rarity = rarity.lower()
            if any(text.lower() in rarity for text in ["knife", "gloves", "extraordinary", "contraband", "★"]):
                ansi_color = '[2;33m'
                rarity = "contraband"
            elif "covert" in rarity:
                ansi_color = '[2;31m'
                rarity = "covert"
            elif "classified" in rarity:
                ansi_color = '[2;35m'
                rarity = "classified"
            elif "restricted" in rarity:
                rarity = "restricted"
            elif "mil-spec" in rarity:
                rarity = "mil_spec"
            elif "industrial grade" in rarity:
                ansi_color = '[2;37m'
                rarity = "industrial_grade"
            elif "consumer grade" in rarity:
                ansi_color = '[2;37m'
                rarity = "consumer_grade"
            else:
                channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)
                await channel.send(content="RARITY detection error!")
                return

        except Exception as err:
            channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)
            await channel.send(content=str(err))
            return

        # Everything ok!

        # Fetch data from discord server
        user = await self.client.fetch_user(user_id)
        channel = await self.client.fetch_channel(1241019624313851969)

        # Create and send image
        with io.BytesIO() as image_binary:
            event = await self.create_image(case_name, image_url, quality, name, rarity, is_stattrak)
            event.save(image_binary, 'PNG')
            image_binary.seek(0)
            result = File(fp=image_binary, filename="event.png")
            content = f"{user.mention}```ansi\nhas opened a container and found: {ansi_color}{name}[0m\n```"
            await channel.send(content=content, file=result)

    @staticmethod
    async def create_image(case_name: str, image_url: str, quality: str, drop_name: str, rarity: str, is_stattrak: bool):
        width = 800
        height = 600

        with Image.open(f"assets/images/cases/backgrounds/{rarity}.png") as image:
            notosans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                         'NotoSans-Bold.ttf')  # NOQA
            notosans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                            'NotoSans-Regular.ttf')  # NOQA

            # ======== Fonts to use =============
            font_normal_bold = truetype(notosans_bold, 36, encoding='UTF-8')
            font_normal = truetype(notosans_regular, 24, encoding='UTF-8')
            font_small_bold = truetype(notosans_bold, 16, encoding='UTF-8')
            font_small = truetype(notosans_regular, 14, encoding='UTF-8')

            white = (255, 255, 255, 255)
            orange = (207, 106, 50, 255)
            grey = (178, 178, 178, 255)

            draw = Draw(image)
            is_star = "★" in drop_name
            title_color = orange if is_stattrak else white
            if is_star:
                drop_name = drop_name[1:]
                unicode_font = truetype("DejaVuSans.ttf", 18)
                draw.text((9, 11), u"\u2605", title_color, font=unicode_font) # Draw star.
                draw.text((20, 10), drop_name, title_color, font=font_small_bold)
            else:
                draw.text((10, 10), drop_name, title_color, font=font_small_bold)

            draw.text((10, 40), quality, grey, font=font_small_bold)


            item_image = Image.open(requests.get(image_url, stream=True).raw)
            image.paste(item_image, (20, 40))


            return image


async def setup(client):
    await client.add_cog(CaseOpening(client))
