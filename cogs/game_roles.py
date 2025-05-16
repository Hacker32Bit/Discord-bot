import os
from typing import Final

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
GUILD_ID: Final[str] = os.getenv("GUILD_ID")


class ButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="CS2", emoji="<:cs2logo:1239536122141605888>", style=discord.ButtonStyle.secondary,
                       custom_id="cs2")
    async def get_cs2_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(1245292520129171466)

        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("add!") # NOQA
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("remove!")  # NOQA

    @discord.ui.button(label="Dota 2", emoji="<:Dota2logo:1239536134451761164>", style=discord.ButtonStyle.secondary,
                       custom_id="dota2")
    async def get_dota2_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(1245292427539910676)

        if role not in interaction.user.roles:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("add!")  # NOQA
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("remove!")  # NOQA


class GameRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Game Roles\" cog is ready!")

    def cog_unload(self):
        print("[INFO] Cog \"Game Roles\" was unloaded!")

    @app_commands.command(name="game_roles", description="Add game role")
    async def game_roles(self, interaction: discord.Interaction):
        print(interaction)
        await interaction.response.send_message(view=ButtonView()) # NOQA


async def setup(bot):
    await bot.add_cog(GameRoles(bot), guilds=[discord.Object(id=GUILD_ID)])
