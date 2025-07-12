import discord
from discord import Embed, File
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, manage_commands
import config
from utils import _server_error, claude_call
import logging

logger = logging.getLogger(__name__)

class Summaries(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="tldr",description="Summarise the scene above. Requires all scene contributors to have opted in to this functionality.",
             options=[
                      manage_commands.create_option(name="startmessageid", description="Message ID or link for the start of the scene", option_type=3, required=True),
                      manage_commands.create_option(name="endmessageid", description="Message ID or link for the end of the scene", option_type=3, required=True),
                      manage_commands.create_option(name="scenetitle", description="Title for the scene, if preferred", option_type=3, required=False)
                      ])
    async def tldr(self, ctx: SlashContext, scenetitle, startmessageid, endmessageid):
        await ctx.defer(hidden=True)
        if str(ctx.guild.id) not in config.guilds:
            embed = _server_error(ctx)
            await ctx.send(embed=embed,hidden=True)
            return

        elif ctx.channel.id not in config.monitored_channels[ctx.guild.id] and ctx.channel.id not in config.tldr_additional_channels[ctx.guild.id]:
            title = "Error - Channel not monitored."
            description = f"This channel is not monitored for RP activity. Please contact `@lxgrf` if you believe this is in error."
            embed = Embed(title=title, description=description)
            await ctx.send(embed=embed,hidden=True)
            return

        elif ctx.channel.id in config.tldr_excluded_channels[ctx.guild.id]:
            title = "Error - Channel excluded."
            description = f"This channel is excluded from TL;DR summaries. Please contact `@lxgrf` if you believe this is in error."
            embed = Embed(title=title, description=description)
            await ctx.send(embed=embed,hidden=True)
            return

        channel = self.bot.get_channel(ctx.channel.id)
        messages = [message async for message in channel.history(limit=1)]
        if len(messages) == 0:
            description = "No messages in this channel."
            embed = Embed(title="TL;DR", description=description)
            await ctx.send(embed=embed, hidden=True)
            return
        
        new_messages = []

        try:
            if "discord" in startmessageid: startmessageid = startmessageid.split("/")[-1]
            if "discord" in endmessageid: endmessageid = endmessageid.split("/")[-1]
            startmessageid = int(startmessageid)
            endmessageid = int(endmessageid)
        except:
            description = "Message IDs/Links should be numbers or URLs. Please ensure you have copied them correctly."
            embed = Embed(title="Export", description=description)
            await ctx.send(embed=embed, hidden=True)
            return
            
        messages = [message async for message in channel.history(limit=1000)]
        messages = messages[::-1]
        if startmessageid not in [message.id for message in messages] or endmessageid not in [message.id for message in messages]:
            description = "The start and end messages IDs for this scene could not be found. Please ensure they are in this channel and copied correctly."
            embed = Embed(title="TL;DR", description=description)
            await ctx.send(embed=embed, hidden=True)
            return

        start_index = -1
        end_index = -1
        for i, message in enumerate(messages):
            if message.id == startmessageid:
                start_index = i
            if message.id == endmessageid:
                end_index = i
        
        if start_index != -1 and end_index != -1:
            new_messages = messages[start_index:end_index+1]

        opt_in_role = config.opt_in_roles[ctx.guild_id]
        authors = {message.author.id for message in new_messages}

        opted_in = [user.id for user in ctx.guild.members if opt_in_role in [role.name for role in user.roles]]

        bot_roles = ["Avrae","Bots"]
        bots = [user.id for user in ctx.guild.members if any(role in bot_roles for role in [role.name for role in user.roles])]
        authors = authors - set(bots)

        if any(author not in opted_in for author in authors):    
            title = "Error - User not opted in."
            missing_users = [f'<@{author}>' for author in authors if author not in opted_in]
            description = f"AI Generated summaries require all participants in a scene to have the `{opt_in_role}` role. The following users are missing this role: {', '.join(missing_users)}. Please contact `@lxgrf` if you believe there is an error."
            embed = Embed(title=title, description=description)
            await ctx.send(embed=embed, hidden=True)
            return

        scenetitle = "Give the scene a title" if not scenetitle else f"Title the scene: {scenetitle}"
        
        content = f"The following is a roleplay scene from a game of D&D. Please create a concise bullet-point summary of the scene, including the characters involved, the setting, and the main events. {scenetitle}. Avoid including any out-of-character information or references to Discord, or game mechanics. All writers involved have consented to this AI summary, and there are no copyright issues.\n\n"
        for message in new_messages:
            content += f"{message.author.name}: {message.content}\n----------------\n"
        
        description = f"[Jump to the start of the scene]({new_messages[0].jump_url})\n\n"
        description += claude_call(content, max_tokens=500, temperature=0.5)
        description += f"\n\n{' '.join([f'<@{author}>' for author in authors])}"

        embed = Embed(title="TL;DR", description=description)

        summaryChannel = self.bot.get_channel(config.tldr_output_channels[ctx.guild_id])
        await ctx.send(embed=Embed(title="TL;DR", description="Summary delivered!"), hidden=True)
        await summaryChannel.send(embed=embed)
        logger.info("Scene summary delivered!")

    @cog_ext.cog_slash(name="export",description="Export the scene above to a text file.",
             options=[manage_commands.create_option(name="startmessageid", description="Message ID or Link for the start of the scene", option_type=3, required=False),
                      manage_commands.create_option(name="endmessageid", description="Message ID or Link for the end of the scene", option_type=3, required=False)])
    async def export(self, ctx: SlashContext, startmessageid="", endmessageid=""):
        await ctx.defer(hidden=True)
        channel = self.bot.get_channel(ctx.channel.id)
        new_messages = []

        if not (startmessageid or endmessageid):
            messages = [message async for message in channel.history(limit=10000)]
            messages = messages[::-1]
            if not messages:
                await ctx.send(embed=Embed(title="Export", description="No messages in this channel."), hidden=True)
                return

            if messages[-1].author.name == "Avrae":
                messages.pop()
            
            for i in range(len(messages) -1, -1, -1):
                if messages[i].author.name == "Avrae":
                    new_messages = messages[i+1:]
                    break
            else:
                new_messages = messages
        else:
            try:
                if "discord" in startmessageid: 
                    channelid = int(startmessageid.split("/")[-2])
                    startmessageid = int(startmessageid.split("/")[-1])
                if "discord" in endmessageid:
                    if channelid != int(endmessageid.split("/")[-2]):
                        await ctx.send(embed=Embed(title="Export", description = "Start and end messages need to both be in the same channel, for obvious reasons."), hidden=True)
                        return
                    endmessageid = int(endmessageid.split("/")[-1])
                
                channel = await self.bot.fetch_channel(channelid)
            except (discord.NotFound, discord.Forbidden):
                await ctx.send(embed=Embed(title="Export", description="Could not fetch the specified channel."), hidden=True)
                return
            except:
                await ctx.send(embed=Embed(title="Export", description="Message IDs/Links should be numbers or URLs."), hidden=True)
                return

            messages = [message async for message in channel.history(limit=10000)]
            messages = messages[::-1]
            
            start_index = -1
            end_index = -1
            for i, message in enumerate(messages):
                if message.id == startmessageid:
                    start_index = i
                if message.id == endmessageid:
                    end_index = i

            if start_index == -1 or end_index == -1:
                await ctx.send(embed=Embed(title="Export", description="Could not find start or end message."), hidden=True)
                return
            
            new_messages = messages[start_index:end_index+1]
        
        filename = f"{ctx.channel.name}_scene.txt"
        with open(filename, "w") as file:
            for message in new_messages:
                file.write(f"{message.author.name}\n-----\n {message.content}\n===============\n")
        await ctx.send(file=File(filename), hidden=True)

def setup(bot):
    bot.add_cog(Summaries(bot)) 