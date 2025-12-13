import math
from random import randint
import discord
from discord.ext import commands
from dotenv import load_dotenv
from typing import Final
import os
import requests
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
import json
import asyncio
import io
from discord import File
from discord.errors import NotFound
import re

load_dotenv()
GIVEAWAYS_CHANNEL_ID: Final[str] = os.getenv("GIVEAWAYS_CHANNEL_ID")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")
GIVEAWAYS_MESSAGE_ID: Final[str] = os.getenv("GIVEAWAYS_MESSAGE_ID")
GIVEAWAYS_MESSAGE_IMAGE_ID: Final[str] = os.getenv("GIVEAWAYS_MESSAGE_IMAGE_ID")


class MembersGiveaway(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Members Giveaway\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Members Giveaway\" was unloaded!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        channel = await self.client.fetch_channel(GIVEAWAYS_CHANNEL_ID)
        log_channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)

        try:
            message = await channel.fetch_message(GIVEAWAYS_MESSAGE_ID)
            image_message = await channel.fetch_message(GIVEAWAYS_MESSAGE_IMAGE_ID)

            limit = message.content.split('be ')[1].split(' subscribers')[0]
            image = await image_message.attachments[0].to_file()
            members_count = message.guild.member_count

            with io.BytesIO() as image_binary:
                giveaway = await self.update_image(image, members_count, limit)
                giveaway.save(image_binary, 'PNG')
                image_binary.seek(0)
                result = File(fp=image_binary, filename="giveaway.png")
                await image_message.edit(content="", attachments=[result])

        except NotFound as err:
            await log_channel.send(content="NO MESSAGES in Activity giveaway!")


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        channel = await self.client.fetch_channel(GIVEAWAYS_CHANNEL_ID)
        log_channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)

        try:
            message = await channel.fetch_message(GIVEAWAYS_MESSAGE_ID)
            image_message = await channel.fetch_message(GIVEAWAYS_MESSAGE_IMAGE_ID)

            limit = message.content.split('be ')[1].split(' subscribers')[0]
            image = await image_message.attachments[0].to_file()
            members_count = message.guild.member_count

            with io.BytesIO() as image_binary:
                giveaway = await self.update_image(image, members_count, limit)
                giveaway.save(image_binary, 'PNG')
                image_binary.seek(0)
                result = File(fp=image_binary, filename="giveaway.png")
                await image_message.edit(content="", attachments=[result])

        except NotFound as err:
            await log_channel.send(content="NO MESSAGES in Activity giveaway!")


    @staticmethod
    async def update_image(image, members_count, limit):
        with Image.open(fp=image.fp) as image:
            notosans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                         'assets',
                                         'NotoSans-Bold.ttf')  # NOQA
            notosans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                            'assets',
                                            'NotoSans-Regular.ttf')  # NOQA

            # ======== Fonts to use =============
            font_normal_bold = truetype(notosans_bold, 40, encoding='UTF-8')
            font_normal = truetype(notosans_regular, 40, encoding='UTF-8')

            white = (255, 255, 255, 255)
            discord_color = (114, 137, 218, 255)
            dark_bg = (40, 43, 48, 255)
            dark_bg2 = (66, 69, 73, 255)

            draw = Draw(image)

            # Reset values and progress bar
            draw.rectangle(((280, 465), (799, 530)), fill=dark_bg2)
            draw.rectangle(((26, 545), (774, 573)), fill=dark_bg)

            # Draw new
            limit_text = f" / {limit}"
            limit_w = draw.textlength(limit_text, font_normal_bold)
            draw.text((774, 479), limit_text, white, font=font_normal_bold, anchor='rt')
            draw.text((774 - limit_w, 486), f"{members_count}", white, font=font_normal, anchor='rt')

            # progress bar
            if int(members_count) >= int(limit):
                width = 774
            else:
                width = math.ceil((748 / int(limit)) * int(members_count)) + 10
                draw.polygon(((width, 545), (width + 28, 545), (width, 573)), fill=discord_color)

            draw.rectangle(((26, 545), (width, 573)), fill=discord_color)
            draw.rectangle(((774, 545), (779, 573)), fill=dark_bg)
            draw.rectangle(((780, 545), (800, 573)), fill=dark_bg2)

            return image

    # Command for create giveaway message
    @commands.command(help="create_giveaway", description="Create giveaway message")
    @commands.has_any_role("Owner", "Admin")
    async def create_giveaway(self, ctx: discord.ext.commands.context.Context, count: int,
                              drop_url: str) -> None:
        log_channel = await self.client.fetch_channel(ADMIN_LOG_CHANNEL_ID)

        try:
            r = requests.get(drop_url + '?l=english')
            while r.status_code == 429:
                sleep_time = randint(1800, 3600)
                await log_channel.send(content=f"Steam error 429. Too many request. Sleeping {sleep_time // 60} minutes before retrying.")
                await asyncio.sleep(sleep_time)
                r = requests.get(drop_url + '?l=english')

            pattern = r"var\s+g_rgAssets\s*=\s*(\{.*?\});"

            match = re.search(pattern, r.text, flags=re.DOTALL)

            if not match:
                await log_channel.send(content="g_rgAssets not found")

            json_string = match.group(1)

            data = json.loads(json_string)
            try:
                for _ in range(3):
                    data = data[next(iter(data))]
            except Exception as err:
                await log_channel.send(content=f"```{err}```")
                try:
                    data = data[0][0]
                except Exception as err2:
                    await log_channel.send(content=f"```{err2}```")

            name = data["name"]
            quality = data["descriptions"][0]["value"].split("Exterior:")[1].strip()
            rarity = data["type"]
            image_url = "https://community.fastly.steamstatic.com/economy/image/" + data["icon_url"]
            is_stattrak = "StatTrak" in rarity
            rarity = rarity.lower()
            if any(text.lower() in rarity for text in ["knife", "gloves", "extraordinary", "contraband", "★"]):
                rarity = "contraband"
            elif "covert" in rarity:
                rarity = "covert"
            elif "classified" in rarity:
                rarity = "classified"
            elif "restricted" in rarity:
                rarity = "restricted"
            elif "mil-spec" in rarity:
                rarity = "mil_spec"
            elif "industrial grade" in rarity:
                rarity = "industrial_grade"
            elif "consumer grade" in rarity:
                rarity = "consumer_grade"
            else:
                await log_channel.send(content="RARITY detection error!")
                return

        except Exception as err:
            await log_channel.send(content=f"```{err}```")
            return

        # Everything ok!
        channel = await self.client.fetch_channel(GIVEAWAYS_CHANNEL_ID)

        # Create and send image
        with io.BytesIO() as image_binary:
            giveaway = await self.create_image(image_url, quality, name, rarity, is_stattrak,
                                               str(ctx.guild.member_count), str(count))
            giveaway.save(image_binary, 'PNG')
            image_binary.seek(0)
            result = File(fp=image_binary, filename="giveaway.png")
            await channel.send(file=result)

    @staticmethod
    async def create_image(image_url: str, quality: str, drop_name: str, rarity: str,
                           is_stattrak: bool, members_count: str, limit: str):
        with Image.open(f"assets/images/giveaways/backgrounds/{rarity}.png") as image:
            notosans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                         'assets',
                                         'NotoSans-Bold.ttf')  # NOQA
            notosans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank',
                                            'assets',
                                            'NotoSans-Regular.ttf')  # NOQA

            # ======== Fonts to use =============
            font_normal_bold = truetype(notosans_bold, 40, encoding='UTF-8')
            font_normal = truetype(notosans_regular, 40, encoding='UTF-8')
            font_small_bold = truetype(notosans_bold, 16, encoding='UTF-8')
            font_small = truetype(notosans_regular, 16, encoding='UTF-8')

            white = (255, 255, 255, 255)
            orange = (207, 106, 50, 255)
            discord_color = (114, 137, 218, 255)

            # Get item image from url and paste
            item_image = Image.open(requests.get(image_url, stream=True).raw)
            item_image = item_image.resize((509, 382))
            image.paste(item_image, (0, 60), item_image.convert("RGBA"))

            draw = Draw(image)
            is_star = "★" in drop_name
            title_color = orange if is_stattrak else white
            if is_star:
                unicode_font = truetype("DejaVuSans.ttf", 18)
                drop_name = drop_name[1:]
                draw.text((9, 11), u"\u2605", title_color, font=unicode_font)  # Draw star.
                draw.text((26, 10), drop_name, title_color, font=font_small_bold)
            else:
                draw.text((10, 10), drop_name, title_color, font=font_small_bold)

            draw.text((10, 33), quality, white, font=font_small)

            # text
            draw.text((22, 390), f"x{len(limit)}", white, font=font_normal_bold)
            draw.text((616, 347), limit, white, font=font_normal_bold)
            limit_text = f" / {limit}"
            limit_w = draw.textlength(limit_text, font_normal_bold)
            draw.text((774, 479), limit_text, white, font=font_normal_bold, anchor='rt')
            draw.text((774 - limit_w, 486), f"{members_count}", white, font=font_normal, anchor='rt')

            # progress bar
            if int(members_count) >= int(limit):
                width = 774
            else:
                width = math.ceil((748 / int(limit)) * int(members_count)) + 10
                draw.polygon(((width, 545), (width + 28, 545), (width, 573)), fill=discord_color)

            draw.rectangle(((26, 545), (width, 573)), fill=discord_color)

            dark_bg = (40, 43, 48, 255)
            dark_bg2 = (66, 69, 73, 255)
            draw.rectangle(((774, 545), (779, 573)), fill=dark_bg)
            draw.rectangle(((780, 545), (800, 573)), fill=dark_bg2)

            return image


async def setup(client):
    await client.add_cog(MembersGiveaway(client))
