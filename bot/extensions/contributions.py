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

        # Aggregate totals
        per_key: Dict[str, int] = defaultdict(int)
        grand_total = 0
        scanned = 0

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
            async for message in channel.history(limit=message_limit, oldest_first=True):
                scanned += 1
                # Build a text blob including content and embed pieces to search for the phrase
                texts: list[str] = []
                if message.content:
                    texts.append(message.content)
                for emb in getattr(message, "embeds", []) or []:
                    if getattr(emb, "title", None):
                        texts.append(emb.title)
                    if getattr(emb, "description", None):
                        texts.append(emb.description)
                    for fld in getattr(emb, "fields", []) or []:
                        if getattr(fld, "name", None):
                            texts.append(str(fld.name))
                        if getattr(fld, "value", None):
                            texts.append(str(fld.value))
                    if getattr(emb, "footer", None) and getattr(emb.footer, "text", None):
                        texts.append(emb.footer.text)

                text_blob = "\n".join(texts)
                if not text_blob:
                    continue

                points_match = self.POINTS_REGEX.search(text_blob)
                if not points_match:
                    continue

                try:
                    points = int(points_match.group(1).replace(",", ""))
                except Exception:
                    continue

                # First word key, now preferring embed title with sensible fallbacks
                first_word = _extract_first_word_key(message)
                if not first_word:
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
            await interaction.followup.send(
                embed=Embed(
                    title="Contribution Points",
                    description="No matching contribution point messages were found in the channel history.",
                )
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
        await interaction.followup.send(embed=embed)

        for idx in range(1, len(chunks)):
            cont_embed = Embed(title=f"Contribution Points Summary (cont. {idx})", description=chunks[idx])
            await interaction.followup.send(embed=cont_embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Contributions(bot))
