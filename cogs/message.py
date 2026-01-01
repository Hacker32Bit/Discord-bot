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


def split_message(text: str, limit: int = DISCORD_LIMIT):
    chunks = []
    current = ""

    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 <= limit:
            current += paragraph + "\n\n"
        else:
            if current:
                chunks.append(current.rstrip())
                current = ""

            while len(paragraph) > limit:
                split_at = paragraph.rfind(" ", 0, limit)
                if split_at == -1:
                    split_at = limit
                chunks.append(paragraph[:split_at])
                paragraph = paragraph[split_at:].lstrip()

            current = paragraph + "\n\n"

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

            for i, chunk in enumerate(chunks):
                content = chunk
                if i == 0 and not is_private:
                    content = f"<@{message.author.id}>,\n{chunk}"

                if is_private:
                    await message.author.send(content)
                else:
                    await message.channel.send(content)

    except Exception as e:
        print(e)


async def setup(client):
    await client.add_cog(Message(client))
