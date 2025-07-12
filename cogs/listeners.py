import re
from discord.ext import commands
import config

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Skip bot messages
        if message.author.bot:
            return
            
        # Check if message is in Silverymoon guild
        if message.guild and message.guild.id == 866376531995918346:
            # Check for "nyoom" with 2+ o's
            if message.channel.id not in config.nyoom_immunity:
                if re.search(r'ny{1,}o{2,}m', message.content.lower()):
                    await message.add_reaction("🏎️")
                    await message.reply("## 🏎️ nyooooom 🏎️")

def setup(bot):
    bot.add_cog(Listeners(bot)) 