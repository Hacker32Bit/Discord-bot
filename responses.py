from random import randint
import g4f
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()

    tell_to_bot = ["hacker.", "bot.", "hacker32bit.", "хакер.", "бот.",
                   "hacker,", "bot,", "hacker32bit,", "хакер,", "бот,",
                   "hacker!", "bot!", "hacker32bit!", "хакер!", "бот!",]
    if any(map(lowered.__contains__, tell_to_bot)):
        print("content:", lowered)

        for i in tell_to_bot:
            lowered = lowered.replace(i, "")

        print("content:", lowered)

        completion = g4f.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": lowered}],
            stream=True,
        )
        result = ""
        for message in completion:
            result += message

        return result
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