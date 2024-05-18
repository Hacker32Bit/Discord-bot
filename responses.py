from random import randint


def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()

    if lowered == "":
        return "Well you\'re awfully silent..."
    elif "hello" in lowered:
        return "Hello there!"
    elif "how are you" in lowered:
        return "I'm good. Thanks!"
    elif "bye" in lowered:
        return "See you!"
    elif "roll" in lowered:
        return f"You rolled: {randint(1, 6)}"
