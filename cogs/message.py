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

    def cog_unload(self):
        print("[INFO] Cog \"Message\" was unloaded!")

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        username: str = str(message.author)
        user_message: str = message.content
        channel: str = str(message.channel)

        print(f"[{datetime.datetime.now()}][{channel}] {username}: {user_message}")

        if message.author == self.client.user:
            return

        activity = getattr(self.client, "current_activity", None)

        await send_message(message, user_message, str(activity) == "I'm ready to discuss")
        # await self.client.process_commands(message)


def split_message(text: str, limit: int = 4000):
    chunks = []
    current = ""

    for line in text.split("\n"):
        # +1 for the newline we add back
        if len(current) + len(line) + 1 <= limit:
            current += line + "\n"
        else:
            if current:
                chunks.append(current.rstrip())
                current = ""

            # line itself is longer than limit → split by spaces
            while len(line) > limit:
                split_at = line.rfind(" ", 0, limit)
                if split_at == -1:
                    split_at = limit
                chunks.append(line[:split_at])
                line = line[split_at:].lstrip()

            current = line + "\n"

    if current:
        chunks.append(current.rstrip())

    return chunks

async def send_message(message, user_message: str, bot_active: bool = False) -> None:

    if not user_message:
        print("(Message was empty because intents were not enabled probably)")
        return

    if is_private := user_message[0] == "?":
        user_message = user_message[1:]

    try:
        selected_chat = message.author if is_private else message.channel
        response: str = await get_response(
            user_message,
            str(message.author.id),
            selected_chat,
            is_private,
            bot_active
        )

        if response:
            chunks = split_message(response)

            for chunk in chunks:
                if is_private:
                    await message.author.send(chunk)
                else:
                    await message.channel.send(chunk)

    except Exception as e:
        print(e)


async def setup(client):
    await client.add_cog(Message(client))
