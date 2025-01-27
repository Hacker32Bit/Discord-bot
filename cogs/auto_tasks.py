import datetime
import os
import io
import sqlite3
from typing import Final
from PIL import Image
from PIL.ImageFont import truetype
from PIL.ImageDraw import Draw
from dateutil.utils import within_delta
from discord.ext import commands, tasks
from discord.errors import NotFound
from discord import File

utc = datetime.timezone.utc
# If no tzinfo is given then UTC is assumed.
time = datetime.time(hour=13, minute=50, tzinfo=utc)

ACTIVITY_GIVEAWAY_CHANNEL_ID: Final[str] = os.getenv("ACTIVITY_GIVEAWAY_CHANNEL_ID")
ACTIVITY_GIVEAWAY_MESSAGE_ID: Final[str] = os.getenv("ACTIVITY_GIVEAWAY_MESSAGE_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()


class AutoTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()
        self.update_activity_giveaways_tables.start()

    def cog_unload(self):
        self.my_task.cancel()
        self.update_activity_giveaways_tables.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"AutoTask\" cog is ready!")

    @tasks.loop(time=time)
    async def my_task(self):
        pass
        # print("Need close server!")

    @staticmethod
    def create_table():
        descending = "SELECT * FROM activity_giveaway WHERE exp ORDER BY exp DESC LIMIT 10"
        cursor.execute(descending)
        result = cursor.fetchall()

        width = 800
        height = 600

        with Image.new(mode='RGBA', size=(width, height), color=(0, 0, 0, 0)) as image:
            notosans_bold = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                         'NotoSans-Bold.ttf')  # NOQA
            notosans_regular = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                            'NotoSans-Regular.ttf')  # NOQA
            rockybilly = os.path.join(os.path.dirname(__file__), os.pardir, 'files_for_copy', 'disrank', 'assets',
                                      'Rockybilly.ttf')  # NOQA

            print(notosans_regular)

            # ======== Fonts to use =============
            font_normal = truetype(notosans_bold, 20, encoding='UTF-8')
            font_small = truetype(notosans_regular, 20, encoding='UTF-8')
            font_signa = truetype(rockybilly, 25, encoding='UTF-8')

            print(font_small)

            h_pos = 0
            new_height = 40

            white = (255, 255, 255, 255)
            black = (0, 0, 0, 255)

            gray_dark = (144, 164, 174, 255)
            gray = (176, 190, 197, 255)

            gray_dark_transparent = (144, 164, 174, 191)
            gray_transparent = (176, 190, 197, 191)

            draw = Draw(image)

            draw.text((5, 3), "Avatar", white, font=font_normal)
            draw.rectangle([(0, h_pos), (width, new_height)], fill=gray_dark_transparent)
            draw.line([(0, new_height - 2), (width, new_height - 2)], fill=gray, width=2)

            image.crop((0, 0, width, new_height))

            for user in result:
                print(user)

            return image

    @tasks.loop(minutes=1)
    async def update_activity_giveaways_tables(self):
        channel = await self.bot.fetch_channel(ACTIVITY_GIVEAWAY_CHANNEL_ID)
        try:
            message = await channel.fetch_message(ACTIVITY_GIVEAWAY_MESSAGE_ID)

            with io.BytesIO() as image_binary:
                self.create_table().save(image_binary, 'PNG')
                image_binary.seek(0)
                result = File(fp=image_binary, filename="table.png")
                await message.edit(content="the new content of the message", attachments=[result])
                print("UPDATE!!!")

        except NotFound as err:
            print("NO MESSAGES")


async def setup(bot):
    await bot.add_cog(AutoTask(bot))
