"""Slash command to create GitHub issues via the GitHub App service."""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import discord
from discord import Embed, app_commands
from discord.ext import commands

import config
from bot.services.github_app import GitHubAppClient, GitHubAppError

logger = logging.getLogger(__name__)


class GitHubIssues(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        services = getattr(bot, "services", None)
        if not services or not getattr(services, "github", None):
            raise RuntimeError("GitHub service not configured on bot instance")
        self.github: GitHubAppClient = services.github

    @app_commands.command(name="issue", description="Create a GitHub issue in the preset repository")
    @app_commands.describe(
        title="Title for the GitHub issue",
        body="Body/content for the GitHub issue",
        label="(optional) Label to apply (name)",
        assignee="(optional) Assignee username (GitHub)",
    )
    async def issue(
        self,
        interaction: discord.Interaction,
        title: str,
        body: str = "",
        label: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        allowed_servers = getattr(config, "ai_enabled_servers", [])
        guild = getattr(interaction, "guild", None)
        guild_id = str(getattr(guild, "id", "")) if guild else None
        if not guild_id or guild_id not in allowed_servers:
            await interaction.followup.send(
                embed=Embed(title="Unavailable", description="This command is not enabled in this server."),
                ephemeral=True,
            )
            return

        repo = getattr(config, "GITHUB_ISSUE_REPO", "")
        if not repo:
            await interaction.followup.send(
                embed=Embed(title="Error", description="GitHub issue repository is not configured."),
                ephemeral=True,
            )
            return

        # Restrict to Dragonspeaker role holders
        member = getattr(interaction, "user", None)
        roles = [role.name for role in getattr(member, "roles", [])]
        if "Dragonspeaker" not in roles:
            await interaction.followup.send(
                embed=Embed(title="Permission denied", description="Only Dragonspeaker role may create issues."),
                ephemeral=True,
            )
            return

        metadata = self._build_metadata(interaction)
        payload_body = (body or "") + metadata

        issue_labels: Optional[Iterable[str]] = None
        if label:
            try:
                labels = self.github.list_labels(repo)
            except GitHubAppError:
                logger.exception("Failed to fetch labels for %s", repo)
                await interaction.followup.send(
                    embed=Embed(title="Error", description="Failed to validate label."),
                    ephemeral=True,
                )
                return

            if label not in labels:
                await interaction.followup.send(
                    embed=Embed(title="Invalid label", description=f"Label '{label}' not found in repository."),
                    ephemeral=True,
                )
                return

            issue_labels = [label]

        issue_assignees: Optional[Iterable[str]] = None
        if assignee:
            try:
                assignees = self.github.list_assignees(repo)
            except GitHubAppError:
                logger.exception("Failed to fetch assignees for %s", repo)
                await interaction.followup.send(
                    embed=Embed(title="Error", description="Failed to validate assignee."),
                    ephemeral=True,
                )
                return

            if assignee not in assignees:
                await interaction.followup.send(
                    embed=Embed(title="Invalid assignee", description=f"Assignee '{assignee}' not found in repository."),
                    ephemeral=True,
                )
                return

            issue_assignees = [assignee]

        try:
            issue = self.github.create_issue(repo, title, payload_body, labels=issue_labels, assignees=issue_assignees)
        except GitHubAppError:
            logger.exception("Failed to create GitHub issue via GitHub App")
            await interaction.followup.send(
                embed=Embed(title="Error", description="Failed to create issue due to an internal error."),
                ephemeral=True,
            )
            return

        issue_url = issue.get("html_url")
        issue_number = issue.get("number")
        title_text = f"Issue #{issue_number} created" if issue_number else "Issue created"
        embed = Embed(title=title_text, description=f"[{title}]({issue_url})" if issue_url else title)
        if issue_url:
            embed.url = issue_url
        if issue_number:
            embed.add_field(name="Issue #", value=str(issue_number), inline=True)

        await interaction.followup.send(content=issue_url or "Issue created", embed=embed, ephemeral=False)
        logger.info("Created GitHub issue %s", issue_url)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _build_metadata(self, interaction: discord.Interaction) -> str:
        author = getattr(interaction, "user", None)
        guild = getattr(interaction, "guild", None)

        author_name = "unknown"
        if author:
            base = getattr(author, "name", getattr(author, "display_name", "unknown"))
            discriminator = getattr(author, "discriminator", None)
            if discriminator and discriminator not in ("0", None):
                author_name = f"{base}#{discriminator}"
            else:
                author_name = base

        guild_name = getattr(guild, "name", None) or str(getattr(guild, "id", "unknown"))
        return f"\n\n---\nThis issue was created via Discord by {author_name} in server: {guild_name}."


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GitHubIssues(bot))
