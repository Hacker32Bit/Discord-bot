import datetime

import discord
from discord.ext import commands
from responses import get_response


class Message(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("[INFO] \"Message\" cog is ready!")

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        username: str = str(message.author)
        user_message: str = message.content
        channel: str = str(message.channel)

        print(f"[{datetime.datetime.now()}][{channel}] {username}: {user_message}")

        if message.author == self.client.user:
            return

        activity = getattr(self.client, "current_activity", None)
        print(activity)

        await send_message(message, user_message, self.client.status == discord.Status.online)
        # await self.client.process_commands(message)


async def send_message(message, user_message: str, bot_active: bool = False) -> None:
    if not user_message:
        print("(Message was empty because intents were not enabled probably)")
        return

    if is_private := user_message[0] == "?":
        user_message = user_message[1:]

    try:
        selected_chat = message.author if is_private else message.channel
        response: str = await get_response(user_message, str(message.author.id), selected_chat, is_private)
        if response:
            await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e)


async def setup(client):
    await client.add_cog(Message(client))
