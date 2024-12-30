from random import randint
import subprocess
from dotenv import load_dotenv
from typing import Final
import os

load_dotenv()
PROJECT_PATH: Final[str] = os.getenv("PROJECT_PATH")

async def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()

    tell_to_bot = ["hacker.", "bot.", "hacker32bit.", "хакер.", "бот.",
                   "hacker,", "bot,", "hacker32bit,", "хакер,", "бот,",
                   "hacker!", "bot!", "hacker32bit!", "хакер!", "бот!", ]
    if any(map(lowered.__contains__, tell_to_bot)):
        for i in tell_to_bot:
            lowered = lowered.replace(i, "")

        result = subprocess.check_output([PROJECT_PATH + "/.venv/bin/python", "scripts/chatGPT.py", "--text",
                                          lowered])

        if result:
            return result.decode("utf-8")

        return "I don't know what happen with me :("
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
