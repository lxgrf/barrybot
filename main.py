from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize bot with Intents
intents = Intents.all()
bot = commands.Bot(command_prefix="\u200b", intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('------')
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

    # Notify lxgrf on startup (once per process) — no fallback logic
    if not getattr(bot, "_startup_dm_sent", False):
        try:
            target_user = await bot.fetch_user(661212031231459329)
            await target_user.send("Barry is online and ready.")
            logger.info("Sent startup DM to lxgrf (661212031231459329)")
        except Exception as e:
            logger.warning(f"Startup DM failed: {e}")
        finally:
            # Ensure we don't spam on reconnects
            bot._startup_dm_sent = True

# Load all cogs
async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            logger.info(f'Loaded extension: {filename[:-3]}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("discord"))

if __name__ == "__main__":
    asyncio.run(main())

