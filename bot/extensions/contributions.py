"""Commands to aggregate contribution points from the Silverymoon downtimes channel."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Dict, Tuple

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
    # Matches: "That's 24 contribution points" or "That's only 24 contribution points"
    POINTS_REGEX = re.compile(r"That\'s\s+(?:only\s+)?(\d+)\s+contribution\s+points", re.IGNORECASE)

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="contributions",
        description="Aggregate contribution points by first-word key from the Silverymoon downtimes channel.",
    )
    @app_commands.describe(message_limit="Number of recent messages to scan (default 500, max 10000).")
    async def contributions(self, interaction: discord.Interaction, message_limit: int = 500) -> None:
        """Scan the configured channel and total contribution points per first-word key.

        Key extraction: first whitespace-delimited word of the message content body.
        Only the message body is scanned (no embed titles, etc.).
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

        try:
            async for message in channel.history(limit=message_limit, oldest_first=True):
                scanned += 1
                content = message.content or ""
                if not content:
                    continue

                points_match = self.POINTS_REGEX.search(content)
                if not points_match:
                    continue

                try:
                    points = int(points_match.group(1))
                except Exception:
                    continue

                # First word of the message content is the key
                stripped = content.lstrip()
                if not stripped:
                    continue
                first_word = stripped.split()[0]
                # Normalise trivial trailing punctuation on first word
                first_word = first_word.strip(".,:;!?—-*")
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
        sorted_totals: Tuple[str, int] = sorted(per_key.items(), key=lambda kv: (-kv[1], kv[0].lower()))  # type: ignore[assignment]

        # Build output, chunk if needed to stay under Discord message limits
        header = (
            f"Grand total: {grand_total} points across {len(per_key)} keys (scanned {scanned} messages / requested {message_limit})."\
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
