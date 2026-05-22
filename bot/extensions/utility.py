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

    @app_commands.command(name="utility", description="In-place server utility command for lxgrf.")
    async def utility(self, interaction: discord.Interaction) -> None:
        """Send a DM to lxgrf containing a list of text channels and their URLs.

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
        # Collect only text channels; skip categories, threads, voice, stage, forum, etc.
        text_channels: Sequence[discord.TextChannel] = guild.text_channels

        # Produce one Markdown line per channel: [Name](url)
        lines: list[str] = []
        for ch in text_channels:
            try:
                channel_url = f"https://discord.com/channels/{guild.id}/{ch.id}"
                lines.append(f"[{ch.name}]({channel_url})")
            except Exception:
                logger.exception("Failed building line for text channel %s", getattr(ch, "id", None))

        # Build DM messages comprised solely of code blocks, chunked under 2000 chars each.
        # Each message is: ```md\n<lines>\n```
        def as_block(content: str) -> str:
            return f"```md\n{content}\n```"

        chunks: list[str] = []
        current_lines: list[str] = []
        for line in lines:
            tentative = "\n".join(current_lines + [line])
            if len(as_block(tentative)) > 2000:
                # flush current
                if current_lines:
                    chunks.append(as_block("\n".join(current_lines)))
                # start new chunk with this line
                current_lines = [line]
            else:
                current_lines.append(line)
        if current_lines:
            chunks.append(as_block("\n".join(current_lines)))

        try:
            target_user = await self.bot.fetch_user(LXGRF_USER_ID)
        except Exception:
            logger.exception("Failed to fetch lxgrf user for utility DM")
            await interaction.followup.send(embed=Embed(title="Error", description="Could not fetch user."))
            return

        sent = 0
        for idx, chunk in enumerate(chunks):
            try:
                # Send each chunk as its own code block message; no headers to keep content clean.
                await target_user.send(chunk)
                sent += 1
            except Exception:
                logger.exception("Failed sending utility DM part %s", idx + 1)

        await interaction.followup.send(
            embed=Embed(
                title="Utility Report", description=f"Sent {sent} DM part(s) to <@{LXGRF_USER_ID}> with {len(lines)} text channel entries."
            ),
            ephemeral=True,
        )

    @app_commands.command(name="senddm", description="Send a custom DM to a server member (lxgrf only).")
    @app_commands.describe(
        user="Server member to DM",
        message="Message content to send",
    )
    async def senddm(self, interaction: discord.Interaction, user: discord.Member, message: str) -> None:
        """Send an owner-only custom DM to a member of the current guild."""
        if interaction.user.id != LXGRF_USER_ID:
            await interaction.response.send_message(
                embed=Embed(title="Not Authorised", description="This command is restricted."),
                ephemeral=True,
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                embed=Embed(title="No Guild Context", description="Run this command in a server."),
                ephemeral=True,
            )
            return

        clean_message = message.strip()
        if not clean_message:
            await interaction.response.send_message(
                embed=Embed(title="Invalid Message", description="Message content cannot be empty."),
                ephemeral=True,
            )
            return

        if len(clean_message) > 2000:
            await interaction.response.send_message(
                embed=Embed(title="Message Too Long", description="Discord DMs support up to 2000 characters per message."),
                ephemeral=True,
            )
            return

        try:
            await user.send(clean_message)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title="DM Failed",
                    description="I couldn't DM that user (their privacy settings may block DMs).",
                ),
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            logger.exception("Failed to send custom DM to user %s", user.id)
            await interaction.response.send_message(
                embed=Embed(title="DM Failed", description=f"Discord API error: {exc}"),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=Embed(title="DM Sent", description=f"Sent your message to {user.mention}."),
            ephemeral=True,
        )

    @app_commands.command(name="sendmessage", description="Send a message in the current channel (lxgrf only).")
    @app_commands.describe(message="Message content to send")
    async def sendmessage(self, interaction: discord.Interaction, message: str) -> None:
        """Send a plain message in the channel where the command is invoked."""
        if interaction.user.id != LXGRF_USER_ID:
            await interaction.response.send_message(
                embed=Embed(title="Not Authorised", description="This command is restricted."),
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=Embed(title="Invalid Channel", description="This command must be run in a text channel."),
                ephemeral=True,
            )
            return

        clean_message = message.strip()
        if not clean_message:
            await interaction.response.send_message(
                embed=Embed(title="Invalid Message", description="Message content cannot be empty."),
                ephemeral=True,
            )
            return

        if len(clean_message) > 2000:
            await interaction.response.send_message(
                embed=Embed(title="Message Too Long", description="Discord messages support up to 2000 characters."),
                ephemeral=True,
            )
            return

        try:
            await interaction.channel.send(clean_message)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(title="Send Failed", description="I don't have permission to send messages in this channel."),
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            logger.exception("Failed to send channel message in %s", interaction.channel.id)
            await interaction.response.send_message(
                embed=Embed(title="Send Failed", description=f"Discord API error: {exc}"),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=Embed(title="Message Sent", description="Your message was posted in this channel."),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:  # pragma: no cover - discord entrypoint
    await bot.add_cog(Utility(bot))
