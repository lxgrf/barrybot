import re
import time
import logging
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
                # For Avrae bot we still may reply with a helpful note (below), but skip general auto-responses
                pass

            # Determine if the author is on IGNORE_LIST; ignored users should not receive direct replies
            is_ignored = False
            try:
                if getattr(config, 'IGNORE_LIST', None) and message.author.id in config.IGNORE_LIST:
                    is_ignored = True
            except Exception:
                # If IGNORE_LIST or author.id isn't available, treat as not ignored
                is_ignored = False

            if message.author.bot and message.author.name.lower() != 'avrae':
                return
            
            # Check for "nyoom" with 2+ o's (only for non-bot messages)
            if not message.author.bot and not is_ignored:
                if message.channel.id not in config.nyoom_immunity:
                    if message.author.name not in config.nyoom_user_immunity:
                        if re.search(r'ny{1,}o{2,}m', message.content.lower()):
                            await message.add_reaction("🏎️")
                            await message.reply("## 🏎️ nyooooom 🏎️")

            # Avrae-specific automated replies (do not ping Dragonspeakers here)
            try:
                if message.author.bot and message.author.name.lower() == 'avrae':
                    text_lower = (message.content or "").lower()
                    # Pattern 1: Go to Marketplace
                    if 'go to marketplace' in text_lower:
                        # concise helpful reply, do not ping role
                        if not is_ignored:
                            await message.reply("It looks like you're trying to use content that D&D Beyond doesn't want you to have. Please ping a `@dragonspeaker` for assistance.\n\nReact with :x: to this message if you'd like to opt out of automated replies")
                    # Pattern 2: account not connected message
                    if "it looks like you don't have your discord account connected to your d&d beyond account" in text_lower:
                        if not is_ignored:
                            await message.reply("It looks like you don't have access to SRD content. Please ping a `@dragonspeaker` for assistance.\n\nReact with :x: to this message if you'd like to opt out of automated replies.")
            except Exception:
                logging.exception("Failed to process Avrae-specific replies")

            # Forward any message that mentions Dragonspeaker role to the Dragonspeaker channel
            try:
                dragonspeaker_role_id = 881993444380258377
                dest_channel_id = 1427377070664847441

                # Skip if message is already in the destination channel
                if message.channel.id != dest_channel_id:
                    # Check role mentions (works even if role is mentioned via @role)
                    if any(role.id == dragonspeaker_role_id for role in getattr(message, 'role_mentions', [])) or f"<@&{dragonspeaker_role_id}>" in message.content:
                        # Don't forward bot messages; allow forwarding even if author is ignored
                        if not message.author.bot:
                            try:
                                dest_channel = self.bot.get_channel(dest_channel_id) or await self.bot.fetch_channel(dest_channel_id)
                                forward_text = f"Forwarded Dragonspeaker mention from <@{message.author.id}> in <#{message.channel.id}>:\n{message.content}\nMessage: {getattr(message, 'jump_url', '')}"
                                await dest_channel.send(forward_text)
                            except Exception:
                                logging.exception("Failed to forward Dragonspeaker mention to destination channel")
            except Exception:
                logging.exception("Error checking for Dragonspeaker mentions in on_message")

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
            # Extract character name from embed description using the "knows X spells" pattern
            character_name = None
            if message.embeds:
                for embed in message.embeds:
                    if embed.description:
                        knows_match = re.search(r"^(.+?) knows \d+ spells?", embed.description)
                        if knows_match:
                            character_name = knows_match.group(1).strip()
                            break
            
            if character_name:
                current_time = time.time()
                
                # Check if this character has been reminded recently
                last_reminder = self.sbb_reminders.get(character_name)
                
                if not last_reminder or (current_time - last_reminder) >= self.sbb_reminder_cooldown:
                    # Send the reminder
                    await message.reply("💡 **Tip:** You can use `!sbb` as a more reliable alias to see your spellbook!\n\nIt should be less confused by homebrew spells and Avrae's weird choices.\n\nIf you would rather not receive this reminder, react to this message with :x: .")
                    
                    # Update the reminder timestamp
                    self.sbb_reminders[character_name] = current_time
                    
                    # Simple confirmation log
                    logging.info(f"Reminded {character_name} of !sbb")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Forward ❌ reactions on this bot's messages in Silverymoon to the Dragonspeaker Ping channel.

        Uses raw events so it works when messages aren't cached.
        """
        try:
            # Only care about reactions in Silverymoon guild
            if payload.guild_id != 866376531995918346:
                return

            # Ignore if reactor is the bot itself
            if payload.user_id == self.bot.user.id:
                return

            # Check for ❌ or common X emoji names
            emoji_name = getattr(payload.emoji, 'name', None)
            if emoji_name not in ("❌", "✖", "x", "X"):
                return

            # Try to fetch the channel and message (may be uncached)
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
            except Exception:
                logging.exception("Failed to fetch channel or message for reaction payload")
                return

            # Only forward reactions that target messages authored by this bot
            if message.author.id != self.bot.user.id:
                return

            # Destination channel to notify (ID provided)
            dest_channel_id = 1427377070664847441
            try:
                dest_channel = self.bot.get_channel(dest_channel_id) or await self.bot.fetch_channel(dest_channel_id)
            except Exception:
                logging.exception(f"Failed to get destination channel {dest_channel_id}")
                return

            author_mention = f"<@{payload.user_id}>"
            origin_channel_mention = f"<#{payload.channel_id}>"
            msg_link = getattr(message, 'jump_url', None) or ''

            # Mention Dragonspeaker role
            dragonspeaker_role_id = 881993444380258377
            role_mention = f"<@&{dragonspeaker_role_id}>"

            # Reply to the original message to acknowledge the request
            try:
                # Don't reply in DMs (shouldn't happen since we checked guild_id above)
                # Also skip acknowledgement if the reactor is in IGNORE_LIST
                reactor_ignored = False
                try:
                    if getattr(config, 'IGNORE_LIST', None) and payload.user_id in config.IGNORE_LIST:
                        reactor_ignored = True
                except Exception:
                    reactor_ignored = False

                if not reactor_ignored and message.channel and getattr(message.channel, 'guild', None):
                    await message.reply(f"Thank you {author_mention} — your request has been noted, and the Dragonspeakers will apply it shortly.")
            except Exception:
                logging.exception("Failed to send acknowledgement reply to the reacted message")

            notify_text = (
                f"{role_mention} ❌ Reaction by {author_mention} on my message in {origin_channel_mention}.\n"
                f"Message: {msg_link}"
            )

            await dest_channel.send(notify_text)

        except Exception:
            logging.exception("Unexpected error in on_raw_reaction_add listener")

def setup(bot):
    bot.add_cog(Listeners(bot)) 

    # Note: on_raw_reaction_add is registered via Cog.listener decorator below