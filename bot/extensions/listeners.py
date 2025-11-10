"""Discord event listeners and automated responses for the Silverymoon guild."""

from __future__ import annotations

import logging
import re
import time
from collections import deque

from discord.ext import commands
import discord

import config
from bot.extensions._helpers.listener_helpers import requires_not_ignored

logger = logging.getLogger(__name__)


class Listeners(commands.Cog):
    SILVERYMOON_GUILD_ID = 866376531995918346
    DRAGONSPEAKER_ROLE_ID = 881993444380258377
    DRAGONSPEAKER_DEST_CHANNEL_ID = 1427377070664847441
    NYOOM_PATTERN = re.compile(r"ny+o{2,}m", re.IGNORECASE)

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sbb_reminders: dict[str, float] = {}
        self.sbb_reminder_cooldown = 24 * 60 * 60
        self.recent_user_messages: dict[int, deque] = {}

    # ------------------------------------------------------------------
    # Recent message tracking + ignore resolution helpers
    # ------------------------------------------------------------------
    def _track_user_message(self, message) -> None:
        if message.author.bot:
            return

        channel_id = message.channel.id
        if channel_id not in self.recent_user_messages:
            self.recent_user_messages[channel_id] = deque(maxlen=10)

        self.recent_user_messages[channel_id].append(
            {
                "user_id": message.author.id,
                "username": message.author.name.lower(),
                "timestamp": time.time(),
            }
        )

    def _get_recent_user_in_channel(self, channel_id, max_age_seconds: int = 10):
        if channel_id not in self.recent_user_messages:
            return None

        current_time = time.time()
        for msg_info in reversed(self.recent_user_messages[channel_id]):
            if current_time - msg_info["timestamp"] <= max_age_seconds:
                return msg_info

        return None

    def _resolve_triggering_user(self, message):
        if not getattr(message, "author", None):
            return None

        if getattr(message.author, "bot", False):
            return self._get_recent_user_in_channel(getattr(message.channel, "id", None))

        return {
            "user_id": message.author.id,
            "username": message.author.name.lower() if getattr(message.author, "name", None) else None,
        }

    def _is_user_ignored(self, user_id=None, username=None) -> bool:
        ignore_list = getattr(config, "IGNORE_LIST", None)
        if not ignore_list:
            return False

        try:
            if user_id is not None and user_id in ignore_list:
                return True
            if username is not None and username in ignore_list:
                return True
        except Exception:
            logger.exception("Failed while checking IGNORE_LIST")

        return False

    # ------------------------------------------------------------------
    # Automated response handlers
    # ------------------------------------------------------------------
    @requires_not_ignored
    async def _handle_nyoom(self, message):
        if message.channel.id in config.nyoom_immunity:
            return
        if message.author.name in config.nyoom_user_immunity:
            return

        content = message.content or ""
        if self.NYOOM_PATTERN.search(content):
            await message.add_reaction("🏎️")
            await message.reply("## 🏎️ nyooooom 🏎️")

    async def _handle_name_alert(self, message):
        content_lower = (message.content or "").lower()
        author_id = getattr(message.author, "id", None)

        # Alerts for lxgrf (661212031231459329): notify if anyone other than lxgrf mentions one of the phrases
        if author_id != 661212031231459329:
            for phrase in ['Sarran', 'Fabian', 'Alex', 'Cerys', 'Afton']:
                if phrase.lower() in content_lower:
                    try:
                        target_user = await self.bot.fetch_user(661212031231459329)
                        alert_text = (
                            f"You were mentioned in Silverymoon by <@{message.author.id}> "
                            f"in <#{message.channel.id}>:\n\n"
                            f"Message: {message.content or '(no content)'}\n"
                            f"Link: {getattr(message, 'jump_url', '') or ''}"
                        )
                        await target_user.send(alert_text)
                        logger.info(
                            "Sent Silverymoon alert DM for phrase '%s' from user %s",
                            phrase,
                            message.author.name,
                        )
                    except Exception:
                        logger.exception("Failed to send Silverymoon alert DM")
                    break

        # Alerts for aethelar (702837629363683408): notify if anyone other than aethelar mentions one of the phrases
        if author_id != 702837629363683408:
            for phrase in ['Mimi', 'Elias', 'Paige']:
                if phrase.lower() in content_lower:
                    try:
                        target_user = await self.bot.fetch_user(702837629363683408)
                        alert_text = (
                            f"You were mentioned in Silverymoon by <@{message.author.id}> "
                            f"in <#{message.channel.id}>:\n\n"
                            f"Message: {message.content or '(no content)'}\n"
                            f"Link: {getattr(message, 'jump_url', '') or ''}"
                        )
                        await target_user.send(alert_text)
                        logger.info(
                            "Sent Silverymoon alert DM to aethelar for phrase '%s' from user %s",
                            phrase,
                            message.author.name,
                        )
                    except Exception:
                        logger.exception("Failed to send Silverymoon alert DM to aethelar")
                    break

    @requires_not_ignored
    async def _handle_avrae_triggers(self, message):
        parts = [message.content or ""]
        if message.embeds:
            for embed in message.embeds:
                try:
                    if getattr(embed, "title", None):
                        parts.append(embed.title)
                    if getattr(embed, "description", None):
                        parts.append(embed.description)
                    if getattr(embed, "footer", None) and getattr(embed.footer, "text", None):
                        parts.append(embed.footer.text)
                    if getattr(embed, "fields", None):
                        for field in embed.fields:
                            parts.append(field.name or "")
                            parts.append(field.value or "")
                except Exception:
                    logger.exception("Failed to parse an embed while checking Avrae triggers")

        text_lower = "\n".join(parts).lower()
        if "this monster's full details" in text_lower:
            return

        if "go to marketplace" in text_lower:
            await message.reply(
                "It looks like you're trying to use content that D&D Beyond doesn't want you to have. "
                "Please try using `!aa` instead of `!a`, and if stuck please ping a `@dragonspeaker` for assistance.\n\n"
                "React with :x: to this message if you'd like to opt out of automated replies"
            )
        if "it looks like you don't have your discord account connected to your d&d beyond account" in text_lower:
            await message.reply(
                "It looks like you don't have access to SRD content. Please try using `!aa` instead of `!a`, and if stuck "
                "please ping a `@dragonspeaker` for assistance.\n\nReact with :x: to this message if you'd like to opt out of automated replies."
            )

    async def _handle_forward_dragonspeaker(self, message):
        if message.channel.id == self.DRAGONSPEAKER_DEST_CHANNEL_ID:
            return

        if not (
            any(role.id == self.DRAGONSPEAKER_ROLE_ID for role in getattr(message, "role_mentions", []))
            or f"<@&{self.DRAGONSPEAKER_ROLE_ID}>" in (message.content or "")
        ):
            return

        if message.author.bot:
            return

        try:
            dest_channel = self.bot.get_channel(self.DRAGONSPEAKER_DEST_CHANNEL_ID) or await self.bot.fetch_channel(
                self.DRAGONSPEAKER_DEST_CHANNEL_ID
            )
        except Exception:
            logger.exception("Failed to fetch Dragonspeaker destination channel")
            return

        jump_url = getattr(message, "jump_url", "") or ""
        prefix = f"Forwarded Dragonspeaker mention from <@{message.author.id}> in <#{message.channel.id}>:\n"
        max_total = 1800
        reserved = len(prefix) + len("\nMessage: ") + len(jump_url) + 3
        content = message.content or ""
        if len(content) + reserved > max_total:
            allowed = max_total - reserved
            content = content[:allowed] + "... (truncated)" if allowed > 0 else "(content omitted - too long)"

        forward_text = f"{prefix}{content}\nMessage: {jump_url}"
        await dest_channel.send(forward_text)

    @requires_not_ignored
    async def _check_spellbook_reminder(self, message):
        spellbook_pattern = r"An italicized spell indicates that the spell is homebrew."

        footer_text = ""
        if message.embeds:
            for embed in message.embeds:
                if getattr(embed, "footer", None) and getattr(embed.footer, "text", None):
                    footer_text += embed.footer.text + " "

        text_to_check = (message.content or "") + " " + footer_text
        if not re.search(spellbook_pattern, text_to_check):
            return

        character_name = None
        if message.embeds:
            for embed in message.embeds:
                if getattr(embed, "description", None):
                    knows_match = re.search(r"^(.+?) knows \d+ spells?", embed.description)
                    if knows_match:
                        character_name = knows_match.group(1).strip()
                        break

        if not character_name:
            return

        current_time = time.time()
        last_reminder = self.sbb_reminders.get(character_name)
        if last_reminder and (current_time - last_reminder) < self.sbb_reminder_cooldown:
            return

        await message.reply(
            "💡 **Tip:** You can use `!sbb` as a more reliable alias to see your spellbook!\n\n"
            "It should be less confused by homebrew spells and Avrae's weird choices.\n\n"
            "-# You will not receive this tip again for 24 hours. If you would rather opt out of automated tips, react to this message with :x: ."
        )
        self.sbb_reminders[character_name] = current_time
        logger.info("Reminded %s of !sbb", character_name)

    # ------------------------------------------------------------------
    # Event listeners
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author == self.bot.user:
            return

        if not message.guild or message.guild.id != self.SILVERYMOON_GUILD_ID:
            return

        if not message.author.bot:
            self._track_user_message(message)

        await self._check_spellbook_reminder(message)

        if message.author.bot and message.author.name.lower() != "avrae":
            return

        if not message.author.bot:
            try:
                await self._handle_nyoom(message)
            except Exception:
                logger.exception("Failed handling nyoom for message %s", getattr(message, "id", None))

        if message.author.bot and message.author.name.lower() == "avrae":
            try:
                await self._handle_avrae_triggers(message)
            except Exception:
                logger.exception("Failed to process Avrae-specific replies")

        try:
            await self._handle_forward_dragonspeaker(message)
        except Exception:
            logger.exception("Error checking for Dragonspeaker mentions in on_message")
            
        if not message.author.bot:
            try:
                await self._handle_name_alert(message)
            except Exception:
                logger.exception("Error handling Silverymoon name alert in on_message")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        try:
            if payload.guild_id != self.SILVERYMOON_GUILD_ID:
                return

            if payload.user_id == self.bot.user.id:
                return

            emoji_name = getattr(payload.emoji, "name", None)
            if emoji_name not in ("❌", "✖", "x", "X"):
                return

            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
            except Exception:
                logger.exception("Failed to fetch channel or message for reaction payload")
                return

            if message.author.id != self.bot.user.id:
                return

            try:
                dest_channel = self.bot.get_channel(self.DRAGONSPEAKER_DEST_CHANNEL_ID) or await self.bot.fetch_channel(
                    self.DRAGONSPEAKER_DEST_CHANNEL_ID
                )
            except Exception:
                logger.exception("Failed to get Dragonspeaker destination channel")
                return

            author_mention = f"<@{payload.user_id}>"
            origin_channel_mention = f"<#{payload.channel_id}>"
            msg_link = getattr(message, "jump_url", None) or ""

            role_mention = f"<@&{self.DRAGONSPEAKER_ROLE_ID}>"

            try:
                reactor_username = None
                try:
                    reactor_user = await self.bot.fetch_user(payload.user_id)
                    reactor_username = reactor_user.name.lower() if reactor_user else None
                except Exception:
                    reactor_username = None

                reactor_ignored = self._is_user_ignored(
                    user_id=payload.user_id,
                    username=reactor_username,
                )

                if not reactor_ignored and message.channel and getattr(message.channel, "guild", None):
                    await message.reply(
                        f"Thank you {author_mention} — your request has been noted, and the Dragonspeakers will apply it shortly."
                    )
            except Exception:
                logger.exception("Failed to send acknowledgement reply to the reacted message")

            notify_text = (
                f"{role_mention} ❌ Reaction by {author_mention} on my message in {origin_channel_mention}.\n"
                f"Message: {msg_link}"
            )

            await dest_channel.send(notify_text)

        except Exception:
            logger.exception("Unexpected error in on_raw_reaction_add listener")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Listeners(bot))
