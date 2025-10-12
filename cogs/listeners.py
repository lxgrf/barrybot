import re
import time
from discord.ext import commands
import config

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Track characters that have been reminded about !sbb
        # Format: {character_name: timestamp}
        self.sbb_reminders = {}
        # Cooldown period in seconds (24 hours)
        self.sbb_reminder_cooldown = 24 * 60 * 60

    @commands.Cog.listener()
    async def on_message(self, message):
        # Skip bot messages
        if message.author.bot:
            return
            
        # Check if message is in Silverymoon guild
        if message.guild and message.guild.id == 866376531995918346:
            # Check for spellbook reminder
            await self._check_spellbook_reminder(message)
            
            # Check for "nyoom" with 2+ o's
            if message.channel.id not in config.nyoom_immunity:
                if re.search(r'ny{1,}o{2,}m', message.content.lower()):
                    await message.add_reaction("🏎️")
                    await message.reply("## 🏎️ nyooooom 🏎️")

    async def _check_spellbook_reminder(self, message):
        """Check if message contains spellbook text and send !sbb reminder if needed."""
        # Look for the specific text pattern about italicized spells
        spellbook_pattern = r"An italicized spell indicates that the spell is homebrew."
        
        if re.search(spellbook_pattern, message.content):
            # Extract character name from title format: "Character Name's Spellbook!"
            title_match = re.search(r"([^']+)'s Spellbook!", message.content)
            
            if title_match:
                character_name = title_match.group(1).strip()
                current_time = time.time()
                
                # Check if this character has been reminded recently
                last_reminder = self.sbb_reminders.get(character_name)
                
                if not last_reminder or (current_time - last_reminder) >= self.sbb_reminder_cooldown:
                    # Send the reminder
                    await message.reply("💡 **Tip:** You can use `!sbb` as a more reliable alias to see your spellbook!\n\nIt should be less confused by homebrew spells and Avrae's weird choices.")
                    
                    # Update the reminder timestamp
                    self.sbb_reminders[character_name] = current_time

def setup(bot):
    bot.add_cog(Listeners(bot)) 