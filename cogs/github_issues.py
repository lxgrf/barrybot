import os
import logging
import requests
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, manage_commands
import config
from discord import Embed

logger = logging.getLogger(__name__)

class GitHubIssues(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="issue", description="Create a GitHub issue in the preset repository",
             options=[
                 manage_commands.create_option(name="title", description="Title for the GitHub issue", option_type=3, required=True),
                 manage_commands.create_option(name="body", description="Body/content for the GitHub issue", option_type=3, required=False),
                 manage_commands.create_option(name="label", description="(optional) Label to apply (name)", option_type=3, required=False),
                 manage_commands.create_option(name="assignee", description="(optional) Assignee username (GitHub)", option_type=3, required=False),
             ])
    async def issue(self, ctx: SlashContext, title: str, body: str = "", label: str = None, assignee: str = None):
        await ctx.defer(hidden=True)

        repo = getattr(config, 'GITHUB_ISSUE_REPO', '')
        if not repo:
            await ctx.send(embed=Embed(title="Error", description="GitHub issue repository is not configured."), hidden=True)
            return

        token = os.getenv('GITHUB_TOKEN')
        if not token:
            await ctx.send(embed=Embed(title="Error", description="GITHUB_TOKEN environment variable not set."), hidden=True)
            return

        # Validate role membership: only allow Dragonspeaker role to use this command
        try:
            member = ctx.author
            roles = [r.name for r in member.roles]
            if 'Dragonspeaker' not in roles:
                await ctx.send(embed=Embed(title="Permission denied", description="Only Dragonspeaker role may create issues."), hidden=True)
                return
        except Exception:
            # If we can't check roles, deny for safety
            await ctx.send(embed=Embed(title="Permission denied", description="Could not verify your roles."), hidden=True)
            return

        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        payload = { 'title': title, 'body': body }

        # Validate label and assignee if provided
        if label:
            try:
                labels_url = f"https://api.github.com/repos/{repo}/labels"
                resp = requests.get(labels_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    labels = [label_item['name'] for label_item in resp.json()]
                    if label not in labels:
                        await ctx.send(embed=Embed(title="Invalid label", description=f"Label '{label}' not found in repository."), hidden=True)
                        return
                    payload['labels'] = [label]
                else:
                    logging.warning(f"Could not fetch labels: {resp.status_code}")
            except Exception:
                logging.exception("Failed to validate label")
                await ctx.send(embed=Embed(title="Error", description="Failed to validate label."), hidden=True)
                return

        if assignee:
            try:
                assignees_url = f"https://api.github.com/repos/{repo}/assignees"
                resp = requests.get(assignees_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    assignees = [a['login'] for a in resp.json()]
                    if assignee not in assignees:
                        await ctx.send(embed=Embed(title="Invalid assignee", description=f"Assignee '{assignee}' not found in repository."), hidden=True)
                        return
                    payload['assignees'] = [assignee]
                else:
                    logging.warning(f"Could not fetch assignees: {resp.status_code}")
            except Exception:
                logging.exception("Failed to validate assignee")
                await ctx.send(embed=Embed(title="Error", description="Failed to validate assignee."), hidden=True)
                return

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                issue_url = data.get('html_url')
                embed = Embed(title="Issue created", description=f"[{title}]({issue_url})")
                await ctx.send(embed=embed, hidden=True)
                logger.info(f"Created GitHub issue {issue_url}")
            else:
                logger.error(f"GitHub API returned {resp.status_code}: {resp.text}")
                await ctx.send(embed=Embed(title="Error creating issue", description=f"GitHub API returned {resp.status_code}"), hidden=True)
        except Exception:
            logger.exception("Failed to create GitHub issue")
            await ctx.send(embed=Embed(title="Error", description="Failed to create issue due to an internal error."), hidden=True)


def setup(bot):
    bot.add_cog(GitHubIssues(bot))

