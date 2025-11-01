import datetime
import logging
import re

import discord
from discord import Embed, app_commands
from discord.ext import commands

import config
from utils import _authorised_user, _server_error, get_recent_messages_reversed

logger = logging.getLogger(__name__)


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="useractivity", description="See the RP activity of users.")
    async def useractivity(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.id not in config.monitored_channels.keys():
            embed = _server_error(interaction)
            await interaction.followup.send(embed=embed)
            return

        authorised = any(role.name in config.authorised_roles for role in interaction.user.roles)
        if not authorised:
            embed = _authorised_user()
            await interaction.followup.send(embed=embed)
            return

        active = [
            user.id
            for user in interaction.guild.members
            if any(role.name in config.include_role for role in user.roles)
            and not any(role.name in config.exclude_role for role in user.roles)
        ]

        one_month_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=config.inactivity_threshold)
        fourteen_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=config.warning_threshold)

        channel_histories_new = {}
        channel_histories_old = {}
        for channel_id in config.monitored_channels[interaction.guild.id]:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue
            old_messages = channel.history(limit=50, after=one_month_ago, before=fourteen_days_ago)
            new_messages = channel.history(limit=50, after=fourteen_days_ago)
            channel_histories_new[channel_id] = new_messages
            channel_histories_old[channel_id] = old_messages

        old_activity = {user: 0 for user in active}
        new_activity = {user: 0 for user in active}

        for messages in channel_histories_new.values():
            async for message in messages:
                if message.author.id in active:
                    new_activity[message.author.id] += 1

        for messages in channel_histories_old.values():
            async for message in messages:
                if message.author.id in active:
                    old_activity[message.author.id] += 1

        total_activity = {user: old_activity[user] + new_activity[user] for user in active}

        new_activity = dict(sorted(new_activity.items(), key=lambda item: item[1]))
        total_activity = dict(sorted(total_activity.items(), key=lambda item: item[1]))

        description = ""
        inactive = {}

        if 0 in total_activity.values():
            description = f":red_circle: No posts in the last {config.inactivity_threshold} days:\n"
            for user, posts in total_activity.items():
                if posts == 0:
                    description += f"<@{user}>: {total_activity[user]}\n"
                    inactive.update({user: 200})
            description += "\n"

        if 0 in new_activity.values():
            description += f":orange_circle: No posts in the last {config.warning_threshold} days:\n"
            for user, posts in new_activity.items():
                if posts == 0 and total_activity[user] > 0:
                    description += f"<@{user}>: {new_activity[user]}\n"
            description += "\n"

        if any(post_count in total_activity.values() for post_count in (1, 2, 3)):
            description += f":yellow_circle: 1-3 posts in the last {config.inactivity_threshold} days:\n"
            for user, posts in total_activity.items():
                if 1 <= posts <= 3:
                    description += f"<@{user}>: {total_activity[user]}\n"
            description += "\n"

        description += f":green_circle: 4+ posts in the last {config.inactivity_threshold} days:\n"
        for user, posts in total_activity.items():
            if posts >= 4:
                description += f"<@{user}>: {total_activity[user]}\n"

        embed = Embed(title="User Activity in RP Channels", description=description)
        await interaction.followup.send(embed=embed)

        if interaction.guild.id == 866376531995918346:
            logger.info("Checking for level-ups in Silverymoon server")
            level_up_channel_ids = [866544281408897024, 866544082331369472, 881218238170665043]
            two_weeks_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)

            try:
                level_ups = []
                for channel_id in level_up_channel_ids:
                    level_up_channel = self.bot.get_channel(channel_id)
                    if level_up_channel:
                        message_limit = 2000 if channel_id == 881218238170665043 else 200
                        async for message in level_up_channel.history(limit=message_limit, after=two_weeks_ago):
                            texts = []
                            if message.content:
                                texts.append(message.content)
                            if message.embeds:
                                for embed_obj in message.embeds:
                                    if getattr(embed_obj, "title", None):
                                        texts.append(embed_obj.title)
                                    if getattr(embed_obj, "description", None):
                                        texts.append(embed_obj.description)
                                    for field in getattr(embed_obj, "fields", []):
                                        if getattr(field, "name", None):
                                            texts.append(str(field.name))
                                        if getattr(field, "value", None):
                                            texts.append(str(field.value))
                                    if getattr(embed_obj, "footer", None) and getattr(embed_obj.footer, "text", None):
                                        texts.append(embed_obj.footer.text)
                                    if getattr(embed_obj, "author", None) and getattr(embed_obj.author, "name", None):
                                        texts.append(embed_obj.author.name)

                            text_blob = "\n".join(texts)

                            patterns = [
                                r"^\s*([^\n]+?)\s+(?:gains\s+[\d,]+\s+Experience\s+and\s+)?levels?\s+up\s+to\s+\*{0,2}(\d{1,2})(?:st|nd|rd|th)\*{0,2}\s+level!?",
                                r"^\s*([^\n]+?)\s+level(?:ed|led)\s+up\s+to\s+\*{0,2}(\d{1,2})(?:st|nd|rd|th)\*{0,2}\s+level!?",
                                r"^\s*([^\n]+?)\s+reaches?\s+level\s+\*{0,2}(\d{1,2})\*{0,2}\b",
                            ]

                            for pattern in patterns:
                                for match in re.findall(pattern, text_blob, re.IGNORECASE | re.MULTILINE):
                                    character_name = match[0].strip()
                                    level = int(match[1])
                                    level_ups.append((character_name, level))

                if level_ups:
                    unique_level_ups = sorted(list(set(level_ups)), key=lambda item: item[1], reverse=True)
                    level_up_description = "Level-ups in the last two weeks:\n" + "\n".join(
                        [f"- {name} reached level {level}!" for name, level in unique_level_ups]
                    )
                    level_up_embed = Embed(title="Recent Level-ups", description=level_up_description)
                    await interaction.followup.send(embed=level_up_embed)
                else:
                    level_up_embed = Embed(title="Recent Level-ups", description="No level-ups found in the last two weeks.")
                    await interaction.followup.send(embed=level_up_embed)
            except Exception as exc:
                logger.error("Error checking level-ups: %s", exc)

        description = ""
        six_months_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=180)

        for channel_id in config.monitored_channels[interaction.guild.id]:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue
            messages = channel.history(limit=500, after=six_months_ago, before=one_month_ago)
            async for message in messages:
                if message.author.id in inactive.keys():
                    time_elapsed = datetime.datetime.now(datetime.timezone.utc) - message.created_at
                    if time_elapsed.days < inactive[message.author.id]:
                        inactive[message.author.id] = int(time_elapsed.days)

        inactive_zero = {user: days for user, days in inactive.items() if days == 200}
        for user in inactive_zero.keys():
            inactive.pop(user)

        if inactive_zero:
            description += (
                "No RP posts in the last 180 days. Please note that this may include brand new users who have yet to post.\n\n"
            )
            for user in inactive_zero.keys():
                description += f"<@{user}>\n"

        if inactive:
            description += "\nPosts in the past, but none in the last 31 days:\n\n"
            for user, days in sorted(inactive.items(), key=lambda item: item[1], reverse=True):
                description += f"<@{user}>: last post {days} days ago.\n"

        if description:
            embed = Embed(title="Inactive User Deep Dive", description=description)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="channelactivity", description="Get the time of the last message in a channel.")
    async def channelactivity(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.id not in config.monitored_channels.keys():
            embed = _server_error(interaction)
            await interaction.followup.send(embed=embed)
            return

        authorised = any(role.name in config.authorised_roles for role in interaction.user.roles)
        if not authorised:
            embed = _authorised_user()
            await interaction.followup.send(embed=embed)
            return

        channel_list = config.monitored_channels[interaction.guild.id]
        description = ""
        active = []
        inactive = []
        stale = []

        for channel_id in channel_list:
            channel = self.bot.get_channel(int(channel_id))
            messages = channel.history(limit=1)
            try:
                message = await messages.__anext__()
            except StopAsyncIteration:
                continue
            message_time = message.created_at
            time_elapsed = datetime.datetime.now(datetime.timezone.utc) - message_time
            author = message.author
            status = ":green_circle:"
            if time_elapsed > datetime.timedelta(days=config.channeltimes[interaction.guild.id]["yellow"]):
                status = ":yellow_circle:"
            if time_elapsed > datetime.timedelta(days=config.channeltimes[interaction.guild.id]["red"]):
                status = ":red_circle:"
                if message.author.name != "Avrae":
                    stale.append(channel_id)

            time_elapsed_str = "Today" if time_elapsed.days == 0 else f"{time_elapsed.days} days ago"
            desc_string = f"{status} <#{channel_id}>: {message_time.strftime('%d/%m/%Y')} ({time_elapsed_str})\n"

            if author.name == "Avrae":
                inactive.append(desc_string)
            else:
                active.append(desc_string)

        if active:
            description = "# Active channels:\n(Channels with an ongoing RP scene)\n\n" + "".join(active)
            embed = Embed(title="Last message", description=description)
            await interaction.followup.send(embed=embed)

        if stale:
            ping_description = "Copy and paste the below for your weekly pinging needs\n\n"
            ping_description += (
                "```\n## Weekly pings!\nAs usual, this is a friendly check in on those scenes which seem to be slowing down."
                " How's it going? How's life? Are you both communicating and happy with the pace of things?"
                " Do you need any help or hand from anyone?\n"
            )

            for channel_id in stale:
                users = []
                channel = self.bot.get_channel(int(channel_id))
                message_history = await get_recent_messages_reversed(channel)
                for message in message_history:
                    if message.author.name == "Avrae":
                        break
                    if message.author.id not in users:
                        users.append(message.author.id)
                users_mentions = ", ".join([f"<@{user}>" for user in users])
                ping_description += f"<#{channel_id}>: ({users_mentions})\n"
            ping_description += "```"
            embed = Embed(title="Ping Post", description=ping_description)
            await interaction.followup.send(embed=embed)
        else:
            embed = Embed(title="Ping Post", description="Good news! No stale channels were found. Everyone is playing nicely!")
            await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Activity(bot))
