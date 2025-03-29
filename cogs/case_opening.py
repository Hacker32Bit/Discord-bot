import discord
from PIL import Image
from discord.ext import commands
from dotenv import load_dotenv
from typing import Final
import os

load_dotenv()
EVENTS_CHANNEL_ID: Final[str] = os.getenv("EVENTS_CHANNEL_ID")


class CaseOpening(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Case opening\" cog is ready!")

    # Command for open case event
    @commands.command()
    @commands.has_any_role("Owner", "Admin")
    async def open_cs_case(self, ctx: discord.ext.commands.context.Context, user_id: str, case_name: str, rarity: str, drop_name: str,
                                 file: discord.Attachment) -> None:

        rarities = {"consumer base white": 'consumer_grade',
                    "industrial lightblue": 'industrial_grade',
                    "rare mil-spec blue": 'mil_spec',
                    "mythical restricted remarkable purple": 'restricted',
                    "legendary classified exotic pink": 'classified',
                    "ancient covert extraordinary red": 'covert',
                    "exceedingly rare special glove knife gold immortal contraband": 'contraband'}

        def find_substring_in_dict(substring, dictionary):
            return [value for key, value in dictionary.items() if substring in key]

        rarity = find_substring_in_dict(rarity, rarities)

        user = self.client.get_user(user_id)

        print("user type", type(user))
        print("user", user)

        channel = await self.client.fetch_channel(1241019624313851969)
        print("user_id: ", user_id)
        print("case_name: ", case_name)
        print("rarity: ", rarity)
        print("drop_name: ", drop_name)
        print("file: ", file)
        result = "" + user_id + case_name + drop_name + rarity
        await channel.send(content=result, file=await file.to_file())

    @staticmethod
    async def create_table(client, case_name: str, quality: str, drop_name: str,):
        width = 800
        height = 600

        with Image.open(f"assets/images/cases/backgrounds/{quality}.png") as image:
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


async def setup(client):
    await client.add_cog(CaseOpening(client))
