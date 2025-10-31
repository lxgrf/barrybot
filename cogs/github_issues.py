import os
import logging
import requests
import discord
from discord import app_commands, Embed
from discord.ext import commands
import config

logger = logging.getLogger(__name__)

class GitHubIssues(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="issue", description="Create a GitHub issue in the preset repository")
    @app_commands.describe(
        title="Title for the GitHub issue",
        body="Body/content for the GitHub issue",
        label="(optional) Label to apply (name)",
        assignee="(optional) Assignee username (GitHub)"
    )
    async def issue(self, interaction: discord.Interaction, title: str, body: str = "", label: str = None, assignee: str = None):
        await interaction.response.defer(ephemeral=True)

        # Restrict command to configured AI-enabled servers
        try:
            allowed = getattr(config, 'ai_enabled_servers', [])
            guild_id_str = str(interaction.guild.id) if getattr(interaction, 'guild', None) else None
            if guild_id_str not in allowed:
                await interaction.followup.send(embed=Embed(title="Unavailable", description="This command is not enabled in this server."), ephemeral=True)
                return
        except Exception:
            # If we can't determine the guild, deny for safety
            await interaction.followup.send(embed=Embed(title="Unavailable", description="Could not verify server eligibility."), ephemeral=True)
            return

        repo = getattr(config, 'GITHUB_ISSUE_REPO', '')
        if not repo:
            await interaction.followup.send(embed=Embed(title="Error", description="GitHub issue repository is not configured."), ephemeral=True)
            return

        token = os.getenv('GITHUB_TOKEN')
        if not token:
            await interaction.followup.send(embed=Embed(title="Error", description="GITHUB_TOKEN environment variable not set."), ephemeral=True)
            return

        # Validate role membership: only allow Dragonspeaker role to use this command
        try:
            member = interaction.user
            roles = [r.name for r in member.roles]
            if 'Dragonspeaker' not in roles:
                await interaction.followup.send(embed=Embed(title="Permission denied", description="Only Dragonspeaker role may create issues."), ephemeral=True)
                return
        except Exception:
            # If we can't check roles, deny for safety
            await interaction.followup.send(embed=Embed(title="Permission denied", description="Could not verify your roles."), ephemeral=True)
            return

        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        # Append context metadata to the issue body so reviewers know where it came from
        invoker = None
        try:
            author = getattr(interaction, 'user', None)
            # In discord.py 2.x, discriminator is deprecated, use global_name or name
            invoker = f"{getattr(author, 'name', getattr(author, 'display_name', 'unknown'))}"
            if hasattr(author, 'discriminator') and author.discriminator not in ('0', None):
                invoker += f"#{author.discriminator}"
        except Exception:
            invoker = 'unknown'

        guild_name = None
        try:
            guild_name = getattr(interaction.guild, 'name', str(getattr(interaction.guild, 'id', 'unknown')))
        except Exception:
            guild_name = 'unknown'

        metadata = f"\n\n---\nThis issue was created via Discord by {invoker} in server: {guild_name}."
        payload = { 'title': title, 'body': (body or '') + metadata }

        # Validate label and assignee if provided
        if label:
            try:
                labels_url = f"https://api.github.com/repos/{repo}/labels"
                resp = requests.get(labels_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    labels = [label_item['name'] for label_item in resp.json()]
                    if label not in labels:
                        await interaction.followup.send(embed=Embed(title="Invalid label", description=f"Label '{label}' not found in repository."), ephemeral=True)
                        return
                    payload['labels'] = [label]
                else:
                    logging.warning(f"Could not fetch labels: {resp.status_code}")
            except Exception:
                logging.exception("Failed to validate label")
                await interaction.followup.send(embed=Embed(title="Error", description="Failed to validate label."), ephemeral=True)
                return

        if assignee:
            try:
                assignees_url = f"https://api.github.com/repos/{repo}/assignees"
                resp = requests.get(assignees_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    assignees = [a['login'] for a in resp.json()]
                    if assignee not in assignees:
                        await interaction.followup.send(embed=Embed(title="Invalid assignee", description=f"Assignee '{assignee}' not found in repository."), ephemeral=True)
                        return
                    payload['assignees'] = [assignee]
                else:
                    logging.warning(f"Could not fetch assignees: {resp.status_code}")
            except Exception:
                logging.exception("Failed to validate assignee")
                await interaction.followup.send(embed=Embed(title="Error", description="Failed to validate assignee."), ephemeral=True)
                return

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                issue_url = data.get('html_url')
                issue_number = data.get('number')
                title_text = f"Issue #{issue_number} created" if issue_number else "Issue created"
                embed = Embed(title=title_text, description=f"[{title}]({issue_url})", url=issue_url)
                if issue_number:
                    embed.add_field(name="Issue #", value=str(issue_number), inline=True)
                # make confirmation visible to all and include the raw URL so Discord can unfurl it
                await interaction.followup.send(content=issue_url, embed=embed, ephemeral=False)
                logger.info(f"Created GitHub issue {issue_url}")
            else:
                logger.error(f"GitHub API returned {resp.status_code}: {resp.text}")
                await interaction.followup.send(embed=Embed(title="Error creating issue", description=f"GitHub API returned {resp.status_code}"), ephemeral=True)
        except Exception:
            logger.exception("Failed to create GitHub issue")
            await interaction.followup.send(embed=Embed(title="Error", description="Failed to create issue due to an internal error."), ephemeral=True)


async def setup(bot):
    await bot.add_cog(GitHubIssues(bot))

