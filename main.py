from discord import Intents
from discord_slash import SlashCommand
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

bot = commands.Bot(command_prefix="\u200b", intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)

warnings.filterwarnings("ignore", category=DeprecationWarning)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(os.getenv("discord"))

