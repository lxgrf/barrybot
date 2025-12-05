"""Commands to aggregate contribution points from the Silverymoon downtimes channel."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Dict

import discord
from discord import Embed, app_commands
from discord.ext import commands

import config
from utils import _authorised_user, _server_error

logger = logging.getLogger(__name__)


class Contributions(commands.Cog):
    """Slash commands for contribution point summaries."""

    SILVERYMOON_GUILD_ID = 866376531995918346
    DOWNTIMES_CHANNEL_ID = 881218238170665043
    # Matches: "That's 24 contribution points" or "That's only 24 contribution points" allowing optional markdown
    # around the number (e.g. **24**, *24*), and optional commas in numbers.
    # Accept both straight and curly apostrophes (’ or ').
    POINTS_REGEX = re.compile(
        r"That[’']s\s+(?:only\s+)?\**\*?_?([0-9]{1,3}(?:,[0-9]{3})*)_?\*?\**\s+contribution\s+points",
        re.IGNORECASE,
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="contributions",
        description="Aggregate contribution points by first-word key from the Silverymoon downtimes channel.",
    )
    @app_commands.describe(message_limit="Number of recent messages to scan (default 500, max 10000).")
    async def contributions(self, interaction: discord.Interaction, message_limit: int = 500) -> None:
        """Scan the configured channel and total contribution points per first-word key.

        Key extraction: prefer the first word of the first embed title; fall back to message content,
        embed description, first field value/name, or footer text.
        Contribution phrase is searched across message content and embed fields.
        """
        await interaction.response.defer()

        # Server checks
        if str(interaction.guild.id) not in config.guilds:
            await interaction.followup.send(embed=_server_error(interaction))
            return

        if interaction.guild.id != self.SILVERYMOON_GUILD_ID:
            await interaction.followup.send(
                embed=Embed(
                    title="Unsupported Server",
                    description=(
                        "This command is only available in the Silverymoon server for the configured downtimes channel."
                    ),
                )
            )
            return

        # Authorisation check (reuse existing pattern)
        authorised = any(role.name in config.authorised_roles for role in interaction.user.roles)
        if not authorised:
            await interaction.followup.send(embed=_authorised_user())
            return

        # Fetch the target channel
        try:
            channel = self.bot.get_channel(self.DOWNTIMES_CHANNEL_ID) or await self.bot.fetch_channel(
                self.DOWNTIMES_CHANNEL_ID
            )
        except Exception:
            logger.exception("Failed to fetch downtimes channel: %s", self.DOWNTIMES_CHANNEL_ID)
            await interaction.followup.send(
                embed=Embed(title="Error", description="Could not access the configured downtimes channel.")
            )
            return

        # Sanitise limit
        if message_limit <= 0:
            message_limit = 1
        if message_limit > 10000:
            message_limit = 10000

        # Quick echo mode: if user asked for 1 message, return a labeled breakdown
        # of the most recent non-bot message's parts (content, embed title/description/fields/footer/author).
        # The bot's own deferred response can appear as the newest message, so skip bot messages.
        if message_limit == 1:
            try:
                last_msg = None
                # scan a small window for the latest non-bot message (lookback 50)
                async for m in channel.history(limit=50, oldest_first=False):
                    # Only skip messages sent by this bot itself; allow other bots (like Avrae) to be processed
                    if getattr(self.bot, "user", None) and m.author.id == self.bot.user.id:
                        continue
                    last_msg = m
                    break

                # fallback: if none found in lookback, use the very last message (even if bot)
                if not last_msg:
                    async for m in channel.history(limit=1, oldest_first=False):
                        last_msg = m
                        break

                if not last_msg:
                    await interaction.followup.send(
                        embed=Embed(title="Last message", description="No messages found in the channel."),
                        ephemeral=True,
                    )
                    return

                def _t(s: str | None, lim: int = 1000) -> str:
                    if s is None:
                        return "(none)"
                    s = str(s)
                    return s if len(s) <= lim else s[: max(0, lim - 3)] + "..."

                echo = Embed(title="Last message breakdown")
                echo.add_field(name="Message ID", value=str(last_msg.id), inline=False)
                echo.add_field(name="Author", value=f"{last_msg.author} ({last_msg.author.id})", inline=False)
                echo.add_field(name="Message content", value=_t(last_msg.content or "(empty)"), inline=False)

                if last_msg.embeds:
                    for idx, emb in enumerate(last_msg.embeds):
                        base = f"Embed {idx}"
                        echo.add_field(name=f"{base} - title", value=_t(getattr(emb, "title", None) or "(none)"), inline=False)
                        echo.add_field(name=f"{base} - description", value=_t(getattr(emb, "description", None) or "(none)"), inline=False)
                        # fields combined
                        f_lines = []
                        for f in getattr(emb, "fields", []) or []:
                            n = getattr(f, "name", "")
                            v = getattr(f, "value", "")
                            f_lines.append(f"**{n}**: {v}")
                        if f_lines:
                            echo.add_field(name=f"{base} - fields", value=_t("\n".join(f_lines), 1000), inline=False)
                        if getattr(emb, "footer", None) and getattr(emb.footer, "text", None):
                            echo.add_field(name=f"{base} - footer", value=_t(emb.footer.text), inline=False)
                        if getattr(emb, "author", None) and getattr(emb.author, "name", None):
                            echo.add_field(name=f"{base} - author", value=_t(emb.author.name), inline=False)

                # Send echo to DM, fall back to channel if DMs are disabled
                try:
                    await interaction.user.send(embed=echo)
                    await interaction.followup.send(
                        embed=Embed(title="Last Message", description="Breakdown sent to your DMs!"),
                        ephemeral=True,
                    )
                except discord.Forbidden:
                    await interaction.followup.send(
                        content="Could not DM you the breakdown (check your privacy settings). Sending here instead:",
                        embed=echo,
                        ephemeral=True,
                    )
                except Exception:
                    logger.exception("Failed to send echo to user %s", interaction.user.id)
                    await interaction.followup.send(
                        embed=Embed(title="Error", description="Failed to send message breakdown."),
                        ephemeral=True,
                    )
                return
            except Exception:
                logger.exception("Failed to fetch or echo last message")
                await interaction.followup.send(
                    embed=Embed(title="Error", description="Failed to fetch or echo last message."),
                    ephemeral=True,
                )
                return

        # Aggregate totals
        per_key: Dict[str, int] = defaultdict(int)
        grand_total = 0
        scanned = 0
        # diagnostics
        non_empty_blobs = 0
        regex_matched = 0
        matched_without_key = 0
        sample_matched_no_key: list[str] = []
        sample_unmatched_blobs: list[str] = []

        def _extract_first_word_key(msg: discord.Message) -> str | None:
            """Return the first word key for aggregation.

            Priority order:
            1) First embed title's first word (common for Avrae outputs)
            2) Message content first word
            3) Embed description first word
            4) First embed field value, then field name
            5) Embed footer text first word
            """
            candidates: list[str] = []
            # 1) Prefer embed title
            for emb in getattr(msg, "embeds", []) or []:
                if getattr(emb, "title", None):
                    candidates.append(emb.title)
                    break  # only need the first embed title
                # Also consider author name if present (less common but may hold key)
                if getattr(emb, "author", None) and getattr(emb.author, "name", None):
                    candidates.append(emb.author.name)
            # 2) Message content
            if msg.content:
                candidates.append(msg.content)
            for emb in getattr(msg, "embeds", []) or []:
                if getattr(emb, "description", None):
                    candidates.append(emb.description)
                # Prefer first field's value then name
                fields = list(getattr(emb, "fields", []) or [])
                if fields:
                    first_field = fields[0]
                    if getattr(first_field, "value", None):
                        candidates.append(str(first_field.value))
                    if getattr(first_field, "name", None):
                        candidates.append(str(first_field.name))
                if getattr(emb, "footer", None) and getattr(emb.footer, "text", None):
                    candidates.append(emb.footer.text)

            def _first_word(text: str) -> str | None:
                # Use first non-empty line
                for line in text.splitlines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    # Remove common markdown bullets/prefixes
                    stripped = stripped.lstrip("*-•–—> #")
                    # Split on whitespace
                    tok = stripped.split()[0]
                    # Strip punctuation/markdown wrappers
                    tok = tok.strip("`*_~.,:;!?—-()[]{}\u200b")
                    return tok or None
                return None

            for c in candidates:
                w = _first_word(c)
                if w:
                    return w
            return None

        try:
            # Fetch the most recent messages (last N). oldest_first=False ensures we get newest -> oldest
            async for message in channel.history(limit=message_limit, oldest_first=False):
                # Skip messages sent by this bot only; we want to process Avrae and other bot outputs.
                if getattr(self.bot, "user", None) and message.author.id == self.bot.user.id:
                    continue
                scanned += 1

                # Build parts using the same approach as listeners._handle_avrae_triggers
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
                            logger.exception("Failed to parse an embed while checking contributions")

                text_blob = "\n".join(parts)
                if not text_blob:
                    continue
                non_empty_blobs += 1

                # Prefer per-embed scanning: many Avrae outputs put the phrase in the embed description
                matched_here = False
                for emb in getattr(message, "embeds", []) or []:
                    emb_desc = getattr(emb, "description", None)
                    if not emb_desc:
                        continue
                    # normalize tiny invisible characters
                    emb_desc_norm = emb_desc.replace("\u200b", "").strip()
                    points_match = self.POINTS_REGEX.search(emb_desc_norm) or (getattr(self, "POINTS_REGEX_FALLBACK", None) and self.POINTS_REGEX_FALLBACK.search(emb_desc_norm))
                    if not points_match:
                        # lowercase fallback
                        points_match = self.POINTS_REGEX.search(emb_desc_norm.lower()) or (getattr(self, "POINTS_REGEX_FALLBACK", None) and self.POINTS_REGEX_FALLBACK.search(emb_desc_norm.lower()))
                    if not points_match:
                        continue

                    # got points in this embed description
                    regex_matched += 1
                    try:
                        points = int(points_match.group(1).replace(",", ""))
                    except Exception:
                        continue

                    # key comes from the first word of the embed title (preferred)
                    emb_title = getattr(emb, "title", None) or ""
                    # normalize title similarly
                    emb_title_norm = emb_title.replace("\u200b", "").strip()
                    first_word = None
                    if emb_title_norm:
                        # take first token and strip punctuation
                        tok = emb_title_norm.splitlines()[0].strip()
                        tok = tok.lstrip("*-•–—> #")
                        tok = tok.split()[0] if tok.split() else ""
                        first_word = tok.strip("`*_~.,:;!?—-()[]{}\u200b") or None

                    if not first_word:
                        # fallback to previous message-level heuristic
                        first_word = _extract_first_word_key(message)

                    if not first_word:
                        matched_without_key += 1
                        if len(sample_matched_no_key) < 5:
                            sample_matched_no_key.append(emb_desc_norm[:300])
                        # continue scanning other embeds in the message
                        continue

                    per_key[first_word] += points
                    grand_total += points
                    matched_here = True
                    # continue scanning other embeds (do not break) to capture multiple contributions in one message

                if not matched_here:
                    # fallback: scan the assembled text blob (legacy behaviour)
                    points_match = self.POINTS_REGEX.search(text_blob) or (getattr(self, "POINTS_REGEX_FALLBACK", None) and self.POINTS_REGEX_FALLBACK.search(text_blob))
                    if not points_match:
                        text_lower = text_blob.lower()
                        points_match = self.POINTS_REGEX.search(text_lower) or (getattr(self, "POINTS_REGEX_FALLBACK", None) and self.POINTS_REGEX_FALLBACK.search(text_lower))
                    if not points_match:
                        if len(sample_unmatched_blobs) < 5:
                            sample_unmatched_blobs.append(text_blob[:300])
                        continue

                    regex_matched += 1
                    try:
                        points = int(points_match.group(1).replace(",", ""))
                    except Exception:
                        continue

                    first_word = _extract_first_word_key(message)
                    if not first_word:
                        matched_without_key += 1
                        if len(sample_matched_no_key) < 5:
                            sample_matched_no_key.append(text_blob[:300])
                        continue

                    per_key[first_word] += points
                    grand_total += points
        except Exception:
            logger.exception("Error while scanning channel history for contributions")
            await interaction.followup.send(
                embed=Embed(
                    title="Error", description="An error occurred while scanning the channel history. Please try again."
                )
            )
            return

        if not per_key:
            # Provide diagnostic information to help debug why no keys were extracted
            diag = Embed(title="Contribution Points — diagnostics")
            diag.description = (
                f"Scanned {scanned} messages (requested {message_limit}).\n"
                f"Non-empty message blobs: {non_empty_blobs}\n"
                f"Regex matches: {regex_matched}\n"
                f"Matches with no key extracted: {matched_without_key}\n"
            )

            def _truncate_for_embed(s: str, limit: int = 1000) -> str:
                if s is None:
                    return ""
                if len(s) <= limit:
                    return s
                return s[: max(0, limit - 3)] + "..."

            if sample_matched_no_key:
                joined = "\n---\n".join(sample_matched_no_key)
                diag.add_field(name="Examples (matched points but no key)", value=_truncate_for_embed(joined, 1000), inline=False)
            if sample_unmatched_blobs:
                joined = "\n---\n".join(sample_unmatched_blobs)
                diag.add_field(name="Examples (no regex match)", value=_truncate_for_embed(joined, 1000), inline=False)

            diag.set_footer(text="If you share one of the example blobs I can refine the regex/key extraction.")
            
            # Send diagnostics to DM, fall back to channel if DMs are disabled
            try:
                await interaction.user.send(embed=diag)
                await interaction.followup.send(
                    embed=Embed(title="Contribution Points", description="Diagnostics sent to your DMs!"),
                    ephemeral=True,
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    content="Could not DM you the diagnostics (check your privacy settings). Sending here instead:",
                    embed=diag,
                    ephemeral=True,
                )
            except Exception:
                logger.exception("Failed to send diagnostics to user %s", interaction.user.id)
                await interaction.followup.send(
                    embed=Embed(title="Error", description="Failed to send diagnostics."),
                    ephemeral=True,
                )
            return

        # Sort by total descending, then key
        sorted_totals: list[tuple[str, int]] = sorted(per_key.items(), key=lambda kv: (-kv[1], kv[0].lower()))

        # Build output, chunk if needed to stay under Discord message limits
        header = (
            f"Grand total: {grand_total} points across {len(per_key)} keys (scanned {scanned} messages / requested {message_limit})."
            "\n\n"
        )
        lines = [f"- {k}: {v}" for k, v in sorted_totals]  # bullet list keeps it compact
        description = header

        # Discord embed description limit is ~4096 chars; chunk if necessary
        chunks = []
        current = description
        for line in lines:
            if len(current) + len(line) + 1 > 3800:  # leave headroom for safety
                chunks.append(current)
                current = ""
            current += ("\n" if current else "") + line
        if current:
            chunks.append(current)

        # Send first chunk as an embed, subsequent chunks as continued embeds
        title = "Contribution Points Summary"
        embed = Embed(title=title, description=chunks[0])
        
        try:
            # Send the results to the user's DMs
            await interaction.user.send(embed=embed)
            for idx in range(1, len(chunks)):
                cont_embed = Embed(title=f"Contribution Points Summary (cont. {idx})", description=chunks[idx])
                await interaction.user.send(embed=cont_embed)
            
            await interaction.followup.send(
                embed=Embed(title="Contribution Points", description="Summary sent to your DMs!"),
                ephemeral=True,
            )
        except discord.Forbidden:
            # Fall back to sending in channel if DMs are disabled
            await interaction.followup.send(
                content="Could not DM you the summary (check your privacy settings). Sending here instead:",
                embed=embed,
            )
            for idx in range(1, len(chunks)):
                cont_embed = Embed(title=f"Contribution Points Summary (cont. {idx})", description=chunks[idx])
                await interaction.followup.send(embed=cont_embed)
        except Exception:
            logger.exception("Failed to send contribution summary to user %s", interaction.user.id)
            await interaction.followup.send(
                embed=Embed(title="Error", description="Failed to send contribution summary."),
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Contributions(bot))
