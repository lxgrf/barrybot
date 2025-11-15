"""Utility command(s) restricted to lxgrf for server introspection."""
from __future__ import annotations

import logging
from typing import Sequence

import discord
from discord import app_commands, Embed
from discord.ext import commands

logger = logging.getLogger(__name__)

LXGRF_USER_ID = 661212031231459329

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="utility", description="List all channels in this server (DM to lxgrf).")
    async def utility(self, interaction: discord.Interaction) -> None:
        """Send a DM to lxgrf containing a list of channels and their jump URLs.

        Only lxgrf can invoke this. If invoked by others, an ephemeral denial is returned.
        """
        # Restrict usage
        if interaction.user.id != LXGRF_USER_ID:
            await interaction.response.send_message(
                embed=Embed(title="Not Authorised", description="This command is restricted."), ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                embed=Embed(title="No Guild Context", description="Run this command in a server."), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        # Collect channels: text + voice + categories + threads for completeness
        channels: Sequence[discord.abc.GuildChannel] = guild.channels  # includes categories, text, voice, stage, forum

        lines: list[str] = []
        for ch in channels:
            try:
                # Build a URL if possible (text-based channels have message jump URL format)
                base_url = f"https://discord.com/channels/{guild.id}/{ch.id}"
                type_name = type(ch).__name__.replace("Channel", "")
                name_display = getattr(ch, "name", str(ch.id))
                lines.append(f"[{type_name}] #{name_display} -> {base_url}")
            except Exception:
                logger.exception("Failed building line for channel %s", getattr(ch, "id", None))

        # Threads (not in guild.channels list until active); include active threads in text channels
        try:
            for ch in channels:
                if isinstance(ch, discord.TextChannel):
                    for thread in ch.threads:
                        thread_url = f"https://discord.com/channels/{guild.id}/{thread.id}"
                        lines.append(f"[Thread] #{thread.name} -> {thread_url}")
        except Exception:
            logger.exception("Failed collecting threads")

        content_header = f"Channel inventory for guild: {guild.name} (ID: {guild.id})\nTotal entries: {len(lines)}\n\n"
        remaining = lines

        # Discord DM content must be <= 2000 chars; chunk responsibly.
        chunks: list[str] = []
        current = content_header
        for line in remaining:
            # +1 for newline
            if len(current) + len(line) + 1 > 1900:  # leave some headroom
                chunks.append(current)
                current = ""
            current += ("\n" if current else "") + line
        if current:
            chunks.append(current)

        try:
            target_user = await self.bot.fetch_user(LXGRF_USER_ID)
        except Exception:
            logger.exception("Failed to fetch lxgrf user for utility DM")
            await interaction.followup.send(embed=Embed(title="Error", description="Could not fetch user."))
            return

        sent = 0
        for idx, chunk in enumerate(chunks):
            try:
                header_prefix = f"[Part {idx+1}/{len(chunks)}]\n" if len(chunks) > 1 else ""
                await target_user.send(header_prefix + chunk)
                sent += 1
            except Exception:
                logger.exception("Failed sending utility DM part %s", idx + 1)

        await interaction.followup.send(
            embed=Embed(
                title="Utility Report", description=f"Sent {sent} DM part(s) to <@{LXGRF_USER_ID}> with {len(lines)} entries."
            ),
            ephemeral=True,
        )

async def setup(bot: commands.Bot) -> None:  # pragma: no cover - discord entrypoint
    await bot.add_cog(Utility(bot))
