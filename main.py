import asyncio
import sys
import os
import logging
from time import strftime

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.presences = True

client = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)

async def load_extensions():
    cogs_path = os.path.join(os.path.dirname(__file__), "cogs")
    if not os.path.isdir(cogs_path):
        print(f"[ERROR] Cogs directory not found: {cogs_path}")
        return
    for filename in os.listdir(cogs_path):
        if filename.endswith(".py"):
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
            except Exception as err:
                print(f"Failed to load {filename}: {err}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

async def run_bot():
    await load_extensions()
    log_dir = os.path.join(os.sep, "tmp", "logs")
    os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(
        filename=os.path.join(log_dir, f"{strftime('%Y-%m-%d %H:%M:%S')}.log"),
        encoding='utf-8',
        mode="a")
    discord.utils.setup_logging(level=logging.INFO, root=False, handler=handler)

    while True:
        try:
            await client.start(TOKEN)
        except (discord.ConnectionClosed, discord.GatewayNotFound, discord.DiscordServerError) as e:
            print(f"[WARN] Connection lost: {e}. Retrying in 10 seconds...")
            await asyncio.sleep(10)
        except KeyboardInterrupt:
            print("Bot stopped by keyboard interrupt")
            break
        except Exception as e:
            print(f"[ERROR] Fatal error: {e}")
            break
        else:
            print("[INFO] client.start() exited cleanly (manual logout?)")
            break

async def shutdown():
    print("Shutting down gracefully...")
    await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Received Ctrl+C. Exiting...")
    finally:
        # No need to cancel tasks manually, asyncio.run handles cleanup
        pass
