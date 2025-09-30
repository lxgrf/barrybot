import datetime
import logging
import re
from discord import Embed
from discord.errors import NoMoreItems
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
import config
from utils import _server_error, _authorised_user, get_recent_messages_reversed

logger = logging.getLogger(__name__)

class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="useractivity", description="See the RP activity of users.")
    async def useractivity(self, ctx: SlashContext):
        await ctx.defer()
        if ctx.guild.id not in config.monitored_channels.keys():
            embed = _server_error(ctx)
            await ctx.send(embed=embed)
            return

        authorised = False
        for role in ctx.author.roles:
            if role.name in config.authorised_roles:
                authorised = True
        if not authorised:
            embed = _authorised_user()
            await ctx.send(embed=embed)
            return

        active = [user.id for user in ctx.guild.members if any(role.name in config.include_role for role in user.roles) and not any(role.name in config.exclude_role for role in user.roles)]

        one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=config.inactivity_threshold)
        fourteen_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=config.warning_threshold)
        
        channel_histories_new = {}
        channel_histories_old = {}
        for channel_id in config.monitored_channels[ctx.guild.id]:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                # Channel not found or inaccessible; skip safely
                continue
            old_messages = channel.history(limit=50, after=one_month_ago, before=fourteen_days_ago)
            new_messages = channel.history(limit=50, after=fourteen_days_ago)
            channel_histories_new[channel_id] = new_messages
            channel_histories_old[channel_id] = old_messages

        old_activity = {user: 0 for user in active}
        new_activity = {user: 0 for user in active}

        for channel_id, messages in channel_histories_new.items():
            async for message in messages:
                if message.author.id in active:
                    new_activity[message.author.id] += 1
            
        for channel_id, messages in channel_histories_old.items():
            async for message in messages:
                if message.author.id in active:
                    old_activity[message.author.id] += 1

        total_activity = {user: old_activity[user] + new_activity[user] for user in active}

        new_activity = {k: v for k, v in sorted(new_activity.items(), key=lambda item: item[1], reverse=False)}
        total_activity = {k: v for k, v in sorted(total_activity.items(), key=lambda item: item[1], reverse=False)}
        
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

        if 1 in total_activity.values() or 2 in total_activity.values() or 3 in total_activity.values():
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
        await ctx.send(embed=embed)

        if ctx.guild.id == 866376531995918346:  # Silverymoon server
            logger.info("Checking for level-ups in Silverymoon server")
            level_up_channel_ids = [866544281408897024, 866544082331369472, 881218238170665043] 
            two_weeks_ago = datetime.datetime.utcnow() - datetime.timedelta(days=14)
            
            try:
                level_ups = []
                for channel_id in level_up_channel_ids:
                    level_up_channel = self.bot.get_channel(channel_id)
                    if level_up_channel:
                        # Use higher limit for high-throughput channel, lower for others
                        message_limit = 2000 if channel_id == 881218238170665043 else 200
                        async for message in level_up_channel.history(limit=message_limit, after=two_weeks_ago):
                            texts = []
                            if message.content:
                                texts.append(message.content)
                            if message.embeds:
                                for e in message.embeds:
                                    if getattr(e, "title", None):
                                        texts.append(e.title)
                                    if getattr(e, "description", None):
                                        texts.append(e.description)
                                    for f in getattr(e, "fields", []):
                                        if getattr(f, "name", None):
                                            texts.append(str(f.name))
                                        if getattr(f, "value", None):
                                            texts.append(str(f.value))
                                    if getattr(e, "footer", None) and getattr(e.footer, "text", None):
                                        texts.append(e.footer.text)
                                    if getattr(e, "author", None) and getattr(e.author, "name", None):
                                        texts.append(e.author.name)

                            text_blob = "\n".join(texts)

                            patterns = [
                                r"^\s*([^\n]+?)\s+(?:gains\s+[\d,]+\s+Experience\s+and\s+)?levels?\s+up\s+to\s+\*{0,2}(\d{1,2})(?:st|nd|rd|th)\*{0,2}\s+level!?",
                                r"^\s*([^\n]+?)\s+level(?:ed|led)\s+up\s+to\s+\*{0,2}(\d{1,2})(?:st|nd|rd|th)\*{0,2}\s+level!?",
                                r"^\s*([^\n]+?)\s+reaches?\s+level\s+\*{0,2}(\d{1,2})\*{0,2}\b",
                            ]

                            for pat in patterns:
                                for match in re.findall(pat, text_blob, re.IGNORECASE | re.MULTILINE):
                                    character_name = match[0].strip()
                                    level = int(match[1])
                                    level_ups.append((character_name, level))
                
                if level_ups:
                    unique_level_ups = sorted(list(set(level_ups)), key=lambda item: item[1], reverse=True)
                    level_up_description = "Level-ups in the last two weeks:\n" + "\n".join([f"- {name} reached level {level}!" for name, level in unique_level_ups])
                    level_up_embed = Embed(title="Recent Level-ups", description=level_up_description)
                    await ctx.send(embed=level_up_embed)
                else:
                    level_up_embed = Embed(title="Recent Level-ups", description="No level-ups found in the last two weeks.")
                    await ctx.send(embed=level_up_embed)
            except Exception as e:
                logger.error(f"Error checking level-ups: {str(e)}")

        description = ""
        six_months_ago = datetime.datetime.utcnow() - datetime.timedelta(days=180)

        for channel_id in config.monitored_channels[ctx.guild.id]:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                # Channel not found or inaccessible; skip safely
                continue
            messages = channel.history(limit=500, after=six_months_ago, before=one_month_ago)
            async for message in messages:
                if message.author.id in inactive.keys():
                    timeElapsed = datetime.datetime.utcnow() - message.created_at
                    if timeElapsed.days < inactive[message.author.id]:
                        inactive[message.author.id] = int(timeElapsed.days)

        inactive_zero = {user: days for user, days in inactive.items() if days == 200}
        for user in inactive_zero.keys():
            inactive.pop(user)

        if len(inactive_zero) > 0:
            description += "No RP posts in the last 180 days. Please note that this may include brand new users who have yet to post.\n\n"
            for user, days in inactive_zero.items():
                description += f"<@{user}>\n"

        if len(inactive) > 0:
            description += "\nPosts in the past, but none in the last 31 days:\n\n"
            for user, days in sorted(inactive.items(), key=lambda item: item[1], reverse=True):
                description += f"<@{user}>: last post {days} days ago.\n"

        if description:
            embed = Embed(title="Inactive User Deep Dive", description=description)
            await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="channelactivity", description="Get the time of the last message in a channel.")
    async def channelactivity(self, ctx: SlashContext):
        await ctx.defer()
        if ctx.guild.id not in config.monitored_channels.keys():
            embed = _server_error(ctx)
            await ctx.send(embed=embed)
            return
        
        authorised = False
        for role in ctx.author.roles:
            if role.name in config.authorised_roles:
                authorised = True
        if not authorised:
            embed = _authorised_user()
            await ctx.send(embed=embed)
            return
        
        channel_list = config.monitored_channels[ctx.guild.id]
        description = ""
        active = []
        inactive = []
        stale = []

        for channel_id in channel_list:
            channel = self.bot.get_channel(int(channel_id))
            messages = channel.history(limit=1)
            try:
                message = await messages.next()
            except NoMoreItems:
                # Channel has no messages; skip reporting
                continue
            messageTime = message.created_at
            timeElapsed = datetime.datetime.utcnow() - messageTime
            author = message.author
            status = ":green_circle:"
            if timeElapsed > datetime.timedelta(days=config.channeltimes[ctx.guild.id]["yellow"]):
                status = ":yellow_circle:"     
            if timeElapsed > datetime.timedelta(days=config.channeltimes[ctx.guild.id]["red"]):
                status = ":red_circle:"
                if message.author.name != "Avrae":
                    stale.append(channel_id)
            
            timeElapsed_str = "Today" if timeElapsed.days == 0 else f"{timeElapsed.days} days ago"
            descString = f"{status} <#{channel_id}>: {messageTime.strftime('%d/%m/%Y')} ({timeElapsed_str})\n"

            if author.name == "Avrae":
                inactive.append(descString)
            else:
                active.append(descString)

        if active:
            description = "# Active channels:\n(Channels with an ongoing RP scene)\n\n" + "".join(active)
            embed = Embed(title="Last message", description=description)
            await ctx.send(embed=embed)

        if stale:
            ping_description = "Copy and paste the below for your weekly pinging needs\n\n"
            ping_description += "```\n## Weekly pings!\nAs usual, this is a friendly check in on those scenes which seem to be slowing down. How's it going? How's life? Are you both communicating and happy with the pace of things? Do you need any help or hand from anyone?\n"
            
            for channel_id in stale:
                users = []
                channel = self.bot.get_channel(int(channel_id))
                message_history = await get_recent_messages_reversed(channel)
                for message in message_history:
                    if message.author.name == "Avrae":
                        break
                    elif message.author.id not in users:
                        users.append(message.author.id)
                users_mentions = ", ".join([f"<@{user}>" for user in users])
                ping_description += f"<#{channel_id}>: ({users_mentions})\n"
            ping_description += "```"
            embed = Embed(title="Ping Post", description=ping_description)
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Ping Post", description="Good news! No stale channels were found. Everyone is playing nicely!")
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Activity(bot)) 