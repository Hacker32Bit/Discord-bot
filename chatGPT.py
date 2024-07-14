from g4f.client import Client
import asyncio
import sys
import argparse

if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Define the parser
parser = argparse.ArgumentParser(description='Short sample app')
parser.add_argument('--text', action="store", dest='text', default="")
args = parser.parse_args()

client = Client()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": args.text}],
)

print(response.choices[0].message.content, flush=True, end="")
