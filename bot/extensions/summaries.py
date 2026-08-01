"""Commands for exporting scene transcripts."""

from __future__ import annotations

import logging

import discord
from discord import Embed, File, app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


class Summaries(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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
                start_message_id = None
                end_message_id = None

                startmessageid = startmessageid.strip()
                endmessageid = endmessageid.strip()

                if startmessageid:
                    if "discord" in startmessageid:
                        channel_id = int(startmessageid.split("/")[-2])
                        start_message_id = int(startmessageid.split("/")[-1])
                    else:
                        start_message_id = int(startmessageid)

                if endmessageid:
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
                        end_message_id = int(endmessageid.split("/")[-1])
                    else:
                        end_message_id = int(endmessageid)

                if start_message_id is None and end_message_id is not None:
                    start_message_id = end_message_id
                if end_message_id is None and start_message_id is not None:
                    end_message_id = start_message_id

                if start_message_id is None or end_message_id is None:
                    await interaction.followup.send(
                        embed=Embed(
                            title="Export",
                            description="Message IDs/Links should be numbers or URLs.",
                        ),
                        ephemeral=True,
                    )
                    return

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

            start_index = next((i for i, message in enumerate(messages) if message.id == start_message_id), -1)
            end_index = next((i for i, message in enumerate(messages) if message.id == end_message_id), -1)

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

        try:
            await interaction.user.send(file=File(filename))
            await interaction.followup.send(
                embed=Embed(title="Export", description="Scene exported and sent to your DMs!"),
                ephemeral=True,
            )
        except discord.Forbidden:
            # Fall back to sending in channel if DMs are disabled
            await interaction.followup.send(
                content="Could not DM you the export (check your privacy settings). Sending here instead:",
                file=File(filename),
                ephemeral=True,
            )
        except Exception:
            logger.exception("Failed to send export file to user %s", interaction.user.id)
            await interaction.followup.send(
                embed=Embed(title="Export Failed", description="An error occurred while sending the file."),
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Summaries(bot))
