import re
import time
import logging
from collections import deque
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
        # Track recent user messages per channel to associate with Avrae responses
        # Format: {channel_id: deque([(user_id, username, timestamp), ...])}
        # We keep the last 10 messages per channel
        self.recent_user_messages = {}

    def _track_user_message(self, message):
        """Track a user message in the channel history for later association with Avrae responses."""
        if message.author.bot:
            return
            
        channel_id = message.channel.id
        
        # Initialize deque for this channel if it doesn't exist
        if channel_id not in self.recent_user_messages:
            self.recent_user_messages[channel_id] = deque(maxlen=10)
        
        # Store user info with timestamp
        self.recent_user_messages[channel_id].append({
            'user_id': message.author.id,
            'username': message.author.name.lower(),
            'timestamp': time.time()
        })

    def _get_recent_user_in_channel(self, channel_id, max_age_seconds=10):
        """Get the most recent user who posted in this channel within the time window.
        
        Args:
            channel_id: The channel ID to check
            max_age_seconds: Maximum age of message in seconds (default 10)
            
        Returns:
            dict with user_id and username, or None if no recent user found
        """
        if channel_id not in self.recent_user_messages:
            return None
            
        current_time = time.time()
        
        # Check messages from most recent to oldest
        for msg_info in reversed(self.recent_user_messages[channel_id]):
            if current_time - msg_info['timestamp'] <= max_age_seconds:
                return msg_info
        
        return None

    def _is_user_ignored(self, user_id=None, username=None):
        """Check if a user is in the IGNORE_LIST.
        
        IGNORE_LIST can contain either user IDs (integers) or usernames (strings).
        
        Args:
            user_id: The user's Discord ID
            username: The user's username (lowercase)
            
        Returns:
            bool: True if user is ignored, False otherwise
        """
        ignore_list = getattr(config, 'IGNORE_LIST', None)
        if not ignore_list:
            return False
            
        try:
            # Check if user_id is in the list (for integer IDs)
            if user_id is not None and user_id in ignore_list:
                return True
            
            # Check if username is in the list (for string usernames)
            if username is not None and username in ignore_list:
                return True
                
        except Exception:
            # If there's any error checking the list, treat as not ignored
            pass
            
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        # Safety check: Never respond to our own messages
        if message.author == self.bot.user:
            return
            
        # Check if message is in Silverymoon guild
        if message.guild and message.guild.id == 866376531995918346:
            # Track user messages for later association with Avrae responses
            if not message.author.bot:
                self._track_user_message(message)
            
            # Check for spellbook reminder (allow bot messages for this)
            await self._check_spellbook_reminder(message)

            if message.author.bot and message.author.name.lower() != 'avrae':
                return
            
            # Check for "nyoom" with 2+ o's (only for non-bot messages)
            if not message.author.bot:
                # Get the actual user (not bot) for ignore checking
                user_id = message.author.id
                username = message.author.name.lower()
                is_ignored = self._is_user_ignored(user_id=user_id, username=username)
                
                if not is_ignored:
                    if message.channel.id not in config.nyoom_immunity:
                        if message.author.name not in config.nyoom_user_immunity:
                            if re.search(r'ny{1,}o{2,}m', message.content.lower()):
                                await message.add_reaction("🏎️")
                                await message.reply("## 🏎️ nyooooom 🏎️")

            # Avrae-specific automated replies (do not ping Dragonspeakers here)
            try:
                if message.author.bot and message.author.name.lower() == 'avrae':
                    # For Avrae messages, we need to find the user who triggered them
                    recent_user = self._get_recent_user_in_channel(message.channel.id)
                    
                    # Check if the triggering user is ignored
                    is_ignored = recent_user and self._is_user_ignored(
                        user_id=recent_user['user_id'],
                        username=recent_user['username']
                    )
                    
                    # Build a combined text blob from content and embed fields for robust detection
                    parts = [message.content or ""]
                    if message.embeds:
                        for embed in message.embeds:
                            try:
                                if getattr(embed, 'title', None):
                                    parts.append(embed.title)
                                if getattr(embed, 'description', None):
                                    parts.append(embed.description)
                                if getattr(embed, 'footer', None) and getattr(embed.footer, 'text', None):
                                    parts.append(embed.footer.text)
                                if getattr(embed, 'fields', None):
                                    for f in embed.fields:
                                        parts.append(f.name or "")
                                        parts.append(f.value or "")
                            except Exception:
                                # If embed parsing fails, skip that embed
                                logging.exception("Failed to parse an embed while checking Avrae triggers")

                    text_lower = "\n".join(parts).lower()
                    # Pattern 1: Go to Marketplace
                    if 'go to marketplace' in text_lower:
                        # concise helpful reply, do not ping role
                        if not is_ignored:
                            await message.reply("It looks like you're trying to use content that D&D Beyond doesn't want you to have. Please try using `!aa` instead of `!a`, and if stuck please ping a `@dragonspeaker` for assistance.\n\nReact with :x: to this message if you'd like to opt out of automated replies")
                    # Pattern 2: account not connected message
                    if "it looks like you don't have your discord account connected to your d&d beyond account" in text_lower:
                        if not is_ignored:
                            await message.reply("It looks like you don't have access to SRD content. Please try using `!aa` instead of `!a`, and if stuck please ping a `@dragonspeaker` for assistance.\n\nReact with :x: to this message if you'd like to opt out of automated replies.")
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
                                jump_url = getattr(message, 'jump_url', '') or ''
                                prefix = f"Forwarded Dragonspeaker mention from <@{message.author.id}> in <#{message.channel.id}>:\n"
                                # Reserve space for jump_url line and a small safety margin
                                max_total = 1800
                                reserved = len(prefix) + len("\nMessage: ") + len(jump_url) + 3
                                content = message.content or ""
                                if len(content) + reserved > max_total:
                                    allowed = max_total - reserved
                                    if allowed > 0:
                                        content = content[:allowed] + "... (truncated)"
                                    else:
                                        content = "(content omitted - too long)"

                                forward_text = f"{prefix}{content}\nMessage: {jump_url}"
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
                
                # Try to get reactor's username for checking
                try:
                    reactor_user = await self.bot.fetch_user(payload.user_id)
                    reactor_username = reactor_user.name.lower() if reactor_user else None
                except Exception:
                    reactor_username = None
                
                reactor_ignored = self._is_user_ignored(
                    user_id=payload.user_id,
                    username=reactor_username
                )

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

async def setup(bot):
    await bot.add_cog(Listeners(bot))