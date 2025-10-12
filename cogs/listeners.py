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
        # Safety check: Never respond to our own messages
        if message.author == self.bot.user:
            return
            
        # Check if message is in Silverymoon guild
        if message.guild and message.guild.id == 866376531995918346:
            # Check for spellbook reminder (allow bot messages for this)
            await self._check_spellbook_reminder(message)
            
            # Skip bot messages for other functionality
            if message.author.bot:
                return
            
            # Check for "nyoom" with 2+ o's (only for non-bot messages)
            if message.channel.id not in config.nyoom_immunity:
                if re.search(r'ny{1,}o{2,}m', message.content.lower()):
                    await message.add_reaction("🏎️")
                    await message.reply("## 🏎️ nyooooom 🏎️")

    async def _check_spellbook_reminder(self, message):
        """Check if message contains spellbook text and send !sbb reminder if needed."""
        # Look for the specific text pattern about italicized spells
        spellbook_pattern = r"An italicized spell indicates that the spell is homebrew."
        
        # Check if the message has embeds and look in footer text
        footer_text = ""
        if message.embeds:
            for embed in message.embeds:
                if embed.footer and embed.footer.text:
                    footer_text += embed.footer.text + " "
        
        # Check both message content and footer text for the pattern
        text_to_check = message.content + " " + footer_text
        
        if re.search(spellbook_pattern, text_to_check):
            # Extract character name from title format: "Character Name's Spellbook!"
            # Check in embed titles first, then message content
            title_match = None
            if message.embeds:
                for embed in message.embeds:
                    if embed.title:
                        title_match = re.search(r"([^']+)'s Spellbook!", embed.title)
                        if title_match:
                            break
            
            # If not found in embed titles, check message content
            if not title_match:
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