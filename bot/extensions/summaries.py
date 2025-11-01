"""Commands for summarising RP scenes and exporting transcripts."""

from __future__ import annotations

import logging

import discord
from discord import Embed, File, app_commands
from discord.ext import commands

import config
from utils import _server_error, claude_call

logger = logging.getLogger(__name__)


class Summaries(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="tldr",
        description="Summarise the scene above. Requires all scene contributors to have opted in to this functionality.",
    )
    @app_commands.describe(
        startmessageid="Message ID or link for the start of the scene",
        endmessageid="Message ID or link for the end of the scene",
        scenetitle="Title for the scene, if preferred",
    )
    async def tldr(
        self,
        interaction: discord.Interaction,
        startmessageid: str,
        endmessageid: str,
        scenetitle: str | None = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        if str(interaction.guild.id) not in config.guilds:
            await interaction.followup.send(embed=_server_error(interaction), ephemeral=True)
            return

        monitored = config.monitored_channels[interaction.guild.id]
        additional = config.tldr_additional_channels[interaction.guild.id]
        excluded = config.tldr_excluded_channels[interaction.guild.id]

        if interaction.channel.id not in monitored and interaction.channel.id not in additional:
            title = "Error - Channel not monitored."
            description = (
                "This channel is not monitored for RP activity. Please contact `@lxgrf` if you believe this is in error."
            )
            await interaction.followup.send(embed=Embed(title=title, description=description), ephemeral=True)
            return

        if interaction.channel.id in excluded:
            title = "Error - Channel excluded."
            description = (
                "This channel is excluded from TL;DR summaries. Please contact `@lxgrf` if you believe this is in error."
            )
            await interaction.followup.send(embed=Embed(title=title, description=description), ephemeral=True)
            return

        channel = self.bot.get_channel(interaction.channel.id)
        messages = [message async for message in channel.history(limit=1)]
        if not messages:
            await interaction.followup.send(embed=Embed(title="TL;DR", description="No messages in this channel."), ephemeral=True)
            return

        try:
            startmessageid = self._normalize_message_id(startmessageid)
            endmessageid = self._normalize_message_id(endmessageid)
        except ValueError:
            await interaction.followup.send(
                embed=Embed(
                    title="Export",
                    description="Message IDs/Links should be numbers or URLs. Please ensure you have copied them correctly.",
                ),
                ephemeral=True,
            )
            return

        history = [message async for message in channel.history(limit=1000)]
        history = history[::-1]
        if startmessageid not in {message.id for message in history} or endmessageid not in {message.id for message in history}:
            await interaction.followup.send(
                embed=Embed(
                    title="TL;DR",
                    description=(
                        "The start and end messages IDs for this scene could not be found. Please ensure they are in this "
                        "channel and copied correctly."
                    ),
                ),
                ephemeral=True,
            )
            return

        start_index = next((i for i, message in enumerate(history) if message.id == startmessageid), -1)
        end_index = next((i for i, message in enumerate(history) if message.id == endmessageid), -1)

        scene_messages = history[start_index : end_index + 1] if start_index != -1 and end_index != -1 else []

        opt_in_role = config.opt_in_roles[interaction.guild_id]
        authors = {message.author.id for message in scene_messages}
        opted_in = [user.id for user in interaction.guild.members if opt_in_role in [role.name for role in user.roles]]

        bot_roles = ["Avrae", "Bots"]
        bots = [user.id for user in interaction.guild.members if any(role in bot_roles for role in [role.name for role in user.roles])]
        authors -= set(bots)

        if any(author not in opted_in for author in authors):
            missing_users = [f"<@{author}>" for author in authors if author not in opted_in]
            await interaction.followup.send(
                embed=Embed(
                    title="Error - User not opted in.",
                    description=(
                        "AI Generated summaries require all participants in a scene to have the "
                        f"`{opt_in_role}` role. The following users are missing this role: {', '.join(missing_users)}. "
                        "Please contact `@lxgrf` if you believe there is an error."
                    ),
                ),
                ephemeral=True,
            )
            return

        prompt_title = "Give the scene a title" if not scenetitle else f"Title the scene: {scenetitle}"

        content = (
            "The following is a roleplay scene from a game of D&D. Please create a concise bullet-point summary of the "
            "scene, including the characters involved, the setting, and the main events. "
            f"{prompt_title}. Avoid including any out-of-character information or references to Discord, or game "
            "mechanics. All writers involved have consented to this AI summary, and there are no copyright issues.\n\n"
        )
        for message in scene_messages:
            content += f"{message.author.name}: {message.content}\n----------------\n"

        description = f"[Jump to the start of the scene]({scene_messages[0].jump_url})\n\n"
        description += claude_call(content, max_tokens=500, temperature=0.5)
        description += f"\n\n{' '.join([f'<@{author}>' for author in authors])}"

        embed = Embed(title="TL;DR", description=description)

        summary_channel = self.bot.get_channel(config.tldr_output_channels[interaction.guild_id])
        await interaction.followup.send(embed=Embed(title="TL;DR", description="Summary delivered!"), ephemeral=True)
        await summary_channel.send(embed=embed)
        logger.info("Scene summary delivered!")

    @app_commands.command(name="export", description="Export the scene above to a text file.")
    @app_commands.describe(
        startmessageid="Message ID or Link for the start of the scene",
        endmessageid="Message ID or Link for the end of the scene",
    )
    async def export(
        self,
        interaction: discord.Interaction,
        startmessageid: str = "",
        endmessageid: str = "",
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        channel = self.bot.get_channel(interaction.channel.id)
        scene_messages = []

        if not (startmessageid or endmessageid):
            messages = [message async for message in channel.history(limit=10000)]
            messages = messages[::-1]
            if not messages:
                await interaction.followup.send(
                    embed=Embed(title="Export", description="No messages in this channel."),
                    ephemeral=True,
                )
                return

            if messages[-1].author.name == "Avrae":
                messages.pop()

            for i in range(len(messages) - 1, -1, -1):
                if messages[i].author.name == "Avrae":
                    scene_messages = messages[i + 1 :]
                    break
            else:
                scene_messages = messages
        else:
            try:
                channel_id = interaction.channel.id
                if "discord" in startmessageid:
                    channel_id = int(startmessageid.split("/")[-2])
                    startmessageid = int(startmessageid.split("/")[-1])
                if "discord" in endmessageid:
                    if channel_id != int(endmessageid.split("/")[-2]):
                        await interaction.followup.send(
                            embed=Embed(
                                title="Export",
                                description="Start and end messages need to both be in the same channel, for obvious reasons.",
                            ),
                            ephemeral=True,
                        )
                        return
                    endmessageid = int(endmessageid.split("/")[-1])

                channel = await self.bot.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden):
                await interaction.followup.send(
                    embed=Embed(title="Export", description="Could not fetch the specified channel."),
                    ephemeral=True,
                )
                return
            except Exception:
                await interaction.followup.send(
                    embed=Embed(title="Export", description="Message IDs/Links should be numbers or URLs."),
                    ephemeral=True,
                )
                return

            messages = [message async for message in channel.history(limit=10000)]
            messages = messages[::-1]

            start_index = next((i for i, message in enumerate(messages) if message.id == int(startmessageid)), -1)
            end_index = next((i for i, message in enumerate(messages) if message.id == int(endmessageid)), -1)

            if start_index == -1 or end_index == -1:
                await interaction.followup.send(
                    embed=Embed(title="Export", description="Could not find start or end message."),
                    ephemeral=True,
                )
                return

            scene_messages = messages[start_index : end_index + 1]

        filename = f"{interaction.channel.name}_scene.txt"
        with open(filename, "w") as handle:
            for message in scene_messages:
                handle.write(f"{message.author.name}\n-----\n {message.content}\n===============\n")

        await interaction.followup.send(file=File(filename), ephemeral=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_message_id(self, value: str) -> int:
        if "discord" in value:
            return int(value.split("/")[-1])
        return int(value)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Summaries(bot))
