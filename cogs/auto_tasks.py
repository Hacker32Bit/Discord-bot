import datetime
import os
import io
import sqlite3
from typing import Final
from PIL import Image
from PIL.ImageFont import truetype
from PIL.ImageDraw import Draw
from discord.ext import commands, tasks
from discord.errors import NotFound
from discord import File
import sys
import asyncio

utc = datetime.timezone.utc
# If no tzinfo is given then UTC is assumed.
time = datetime.time(hour=2, minute=0, second=0, tzinfo=utc)

ACTIVITY_GIVEAWAY_CHANNEL_ID: Final[str] = os.getenv("ACTIVITY_GIVEAWAY_CHANNEL_ID")
ACTIVITY_GIVEAWAY_MESSAGE_ID: Final[str] = os.getenv("ACTIVITY_GIVEAWAY_MESSAGE_ID")
ADMIN_LOG_CHANNEL_ID: Final[str] = os.getenv("ADMIN_LOG_CHANNEL_ID")

database = sqlite3.connect("database.sqlite")
cursor = database.cursor()


class AutoTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()
        self.update_activity_giveaways_tables.start()
        self.reboot.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Auto Task\" cog is ready!")
        description = f"```Bot was logged in```"

        channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)  # admin log channel
        await channel.send(description)

    def cog_unload(self):
        self.my_task.cancel()
        self.update_activity_giveaways_tables.cancel()
        self.reboot.cancel()
        print("[INFO] Cog \"Auto Task\" was unloaded!")

    async def perform_shutdown(self):
        await self.bot.close()
        sys.exit(0)

    @tasks.loop(time=time)
    async def my_task(self):
        pass
        # print("Need close server!")

    @tasks.loop(time=time)
    async def reboot(self):
        print("Need close server!")
        channel = await self.bot.fetch_channel(ADMIN_LOG_CHANNEL_ID)
        try:
            # Write intent for backup script
            with open("/tmp/bot_action", "w") as f:
                f.write("reboot")

            description = f"```Daily reboot initiated. Backing up and restarting...```"

            await channel.send(description)

            # Shutdown outside of task loop to avoid hanging
            loop = asyncio.get_running_loop()
            loop.call_soon(asyncio.create_task, self.perform_shutdown())

        except Exception as e:
            await channel.send(e)

    @staticmethod
    async def create_table(client):
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

            place = 0

            for user in result:
                h_pos += 56
                new_height += 56
                place += 1

                color = gray_transparent
                border_color = gray

                if place == 1:
                    h_pos = 40

                if place == 1 and user[2] >= 1000:  # GOLD color
                    color = (255, 193, 7, 191)
                    border_color = (255, 193, 7, 255)
                elif place == 2 and user[2] >= 1000:  # SILVER color
                    color = (158, 158, 158, 191)
                    border_color = (158, 158, 158, 255)
                elif place == 3 and user[2] >= 1000:  # BRONZE color
                    color = (121, 85, 72, 191)
                    border_color = (121, 85, 72, 255)

                user_data = await client.fetch_user(user[0])

                file = await user_data.display_avatar.to_file()
                avatar = Image.open(fp=file.fp)
                avatar = avatar.resize((54, 54))

                # Transform and calculate text width
                transformed_place = str(place)
                w = draw.textlength(transformed_place, font=font_normal_large)

                draw.rectangle([(0, h_pos), (width, h_pos + 56)], fill=color)
                draw.text((27 - w / 2, h_pos + 1), transformed_place, white, font=font_normal_large)
                image.paste(avatar, (59, h_pos))
                # draw.text((59, h_pos + 1), "av", white, font=font_small)
                draw.text((133, h_pos + 1), user_data.name, white, font=font_small_large)

                transformed_xp = str(user[2])

                if user[2] >= 1000:
                    # Transform and calculate text width
                    w = draw.textlength(transformed_xp, font=font_normal)
                    draw.text((width - 37 - w / 2, h_pos + 6), transformed_xp, white, font=font_normal)
                else:
                    # Transform and calculate text width
                    w = draw.textlength(transformed_xp, font=font_small)
                    draw.text((width - 37 - w / 2, h_pos + 6), transformed_xp, white, font=font_small)
                draw.line([(0, h_pos + 54), (width, h_pos + 54)], fill=border_color, width=2)

            image = image.crop((0, 0, width, new_height))
            return image

    @tasks.loop(hours=1)
    async def update_activity_giveaways_tables(self):
        channel = await self.bot.fetch_channel(ACTIVITY_GIVEAWAY_CHANNEL_ID)
        try:
            message = await channel.fetch_message(ACTIVITY_GIVEAWAY_MESSAGE_ID)

            with io.BytesIO() as image_binary:
                table = await self.create_table(self.bot)
                table.save(image_binary, 'PNG')
                image_binary.seek(0)
                result = File(fp=image_binary, filename="table.png")
                await message.edit(content="", attachments=[result])

        except NotFound as err:
            print("NO MESSAGES in Activity giveaway!")


async def setup(bot):
    await bot.add_cog(AutoTask(bot))
