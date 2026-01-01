from random import randint
import asyncio

import discord
from dotenv import load_dotenv
from typing import Final
import os

load_dotenv()
PROJECT_PATH: Final[str] = os.getenv("PROJECT_PATH")


async def get_response(user_input: str, user_id: str, selected_chat: discord.TextChannel,
                       is_private: bool = False, bot_active: bool = False) -> str:
    lowered: str = user_input.lower().strip()

    triggers = tuple("hacker.", "bot.", "hacker32bit.", "хакер.", "бот.",
                   "hacker,", "bot,", "hacker32bit,", "хакер,", "бот,",
                   "hacker!", "bot!", "hacker32bit!", "хакер!", "бот!")

    if lowered.startswith(triggers):
        async with selected_chat.typing():
            for t in triggers:
                if lowered.startswith(t):
                    text = user_input[len(t):].lstrip()

            print("Final text for g4f:", text)

            # Run the subprocess asynchronously (non-blocking)
            process = await asyncio.create_subprocess_exec(
                PROJECT_PATH + "/.venv/bin/python",
                "scripts/chatGPT.py",
                "--user",
                "--uid", str(user_id),
                "--text", text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                return stdout.decode("utf-8")
            elif stderr:
                return f"⚠️ Error: {stderr.decode('utf-8')}"
            else:
                return "I don't know what happened with me :("
    elif bot_active and len(user_input) > 2 and user_input[0] != "!":
        async with selected_chat.typing():
            # Run the subprocess asynchronously (non-blocking)
            process = await asyncio.create_subprocess_exec(
                PROJECT_PATH + "/.venv/bin/python",
                "scripts/chatGPT.py",
                "--no-user",
                "--uid", str(selected_chat.id),
                "--text", user_input,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if stdout:
                return stdout.decode("utf-8")
            elif stderr:
                return f"⚠️ Error: {stderr.decode('utf-8')}"
            else:
                return "I don't know what happened with me :("
    elif lowered == "":
        return "Well you\'re awfully silent..."
    elif "hello" in lowered:
        return "Hello there!"
    elif "how are you" in lowered:
        return "I'm good. Thanks!\nHow are you?"
    elif "bye" in lowered:
        return "See you!"
    elif "roll" in lowered:
        return f"You rolled: {randint(1, 6)}"
