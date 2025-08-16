from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, manage_commands
import config
from utils import _server_error, claude_call, _ai_enabled_server

class Prompts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.",
             options=[manage_commands.create_option(name="first_character", description="Details of the first character in the scene - the more the better", option_type=3, required=True),
                      manage_commands.create_option(name="second_character", description="Details of the second character in the scene - the more the better", option_type=3, required=True),
                      manage_commands.create_option(name="request", description="Any specific requests for the scene prompt.", option_type=3, required=False)])
    async def scene(self, ctx: SlashContext,first_character,second_character,request=""):
        await ctx.defer()
        description = ""
        if str(ctx.guild.id) not in config.guilds:
            embed = _server_error(ctx)
            await ctx.send(embed=embed)
            return
        elif not _ai_enabled_server(ctx.guild.id):
            embed = Embed(title="AI Not Enabled", description="This server does not have AI capabilities enabled. Please contact an administrator if you believe this is in error.")
            await ctx.send(embed=embed)
            return
        elif len(first_character.split(" ")) < 5 or len(second_character.split(" ")) < 5:
            description += "Ok, I'll be honest, I haven't read your scenes.\n\nCan you tell me a little more about these characters, to help me provide a detailed scene for you? For example, `Bob, a grumpy retired carpenter who misses his daughter` is much easier for me to work with than just `Bob`. I have done my best, but the scene I have generated may not fit your expectations.\n\n"
        
        title = "Here is your scene prompt!"
        city = config.guilds[str(ctx.guild.id)]
        description += f"**First character**: `{first_character}`\n**Second character**: `{second_character}`"
        prompt = f"You are a D&D Dungeonmaster. Give a concise bullet-point summary of an idea for a low-stakes encounter, for a roleplay scene between two D&D characters in {city}. The first character is {first_character}, and the second character is {second_character}. Avoid creating backstory for these characters, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than four bullet points."
        if request != "": 
            prompt += f" {request}."
            description += f"\n**Request**: `{request}`"
        
        description += f"\n\n{claude_call(prompt,max_tokens=350)}"

        footer = f"/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with Anthropic Claude."
        embed = Embed(title=title, description=description, footer=footer)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="solo", description="Get a solo prompt! Describe the character involved specifying any relevant detail.",
             options=[manage_commands.create_option(name="character", description="Details of a character in the scene - the more the better", option_type=3, required=True),
                      manage_commands.create_option(name="request", description="Any specific requests for the scene prompt.", option_type=3, required=False)])
    async def solo(self, ctx: SlashContext,character,request=""):
        await ctx.defer()
        description = ""
        if str(ctx.guild.id) not in config.guilds:
            embed = _server_error(ctx)
            await ctx.send(embed=embed)
            return
        elif not _ai_enabled_server(ctx.guild.id):
            embed = Embed(title="AI Not Enabled", description="This server does not have AI capabilities enabled. Please contact an administrator if you believe this is in error.")
            await ctx.send(embed=embed)
            return
        elif len(character.split(" ")) < 5:
            description += "Ok, I'll be honest, I haven't read your scenes.\n\nCan you tell me a little more about this character, to help me provide a detailed scene for you? For example, `Bob, a grumpy retired carpenter who misses his daughter` is much easier for me to work with than just `Bob`.\n\n"
            
        title = "Here is your solo scene prompt!"
        city = config.guilds[str(ctx.guild.id)]
        description += f"**Character**: `{character}`"
        prompt = f"Give a short, concise, bullet-point summary of an idea for an emotive and interesting character development scene for a D&D character in {city}. The character is {character}. Avoid creating backstory for this character, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than 3 bullet points."
        if request != "": 
            prompt += f" {request}."
            description += f"\n**Request**: `{request}`"

        description += f"\n\n{claude_call(prompt)}"
        footer = f"/solo | Request your own solo scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with Anthropic's Claude AI."
        embed = Embed(title=title, description=description, footer=footer)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="help", description="Get help with the Scene Prompt bot.")
    async def help(self, ctx: SlashContext):  
        await ctx.defer()
        title = "AI Suggestions Help"
        description = "This bot generates scene ideas based on brief character descriptions you supply. It uses the Anthropic Claude API to generate text, and the Discord API to send it to you."
        description += "\nNote that any detail supplied may be used, so mentioning that your character is a thief ups the chances of the scene involving theft. Hold back detail you don't want to see."
        description += "\n\n## Commands"
        description += "\n`/scene` - Get a scene prompt! Describe the characters involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
        description += "\n`/solo` - Get a solo prompt! Describe the character involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
        description += "\n\n## Example Usage"
        description += "\n\n**Bad Usage**:\n `/scene first_character:Dave, second_character:Geraldine`\n It might be clear to you who Dave and Geraldine are, but the bot doesn't know. It will do its best, but will generate a prompt that may not fit your expectations."
        description += "\n\n**Good Usage**:\n `/scene first_character:Dave, a retired carpenter who wants to reconcile with his estranged daughter but is too proud to admit fault, character 2:Geraldine, Dave's daughter, who is a successful merchant and has no time for her father's nonsense`\n This description is much more detailed, and the bot will be able to generate a prompt that fits your expectations."
        description += f"\n\nThe bot is currently in beta, using Anthropic's Claudea, so please report any bugs or suggestions to @lxgrf. \n\n`Guild ID: {ctx.guild.id}`"
        
        # Add AI capability status to help command
        if _ai_enabled_server(ctx.guild.id):
            description += "\n\n✅ **AI Capabilities: Enabled**"
        else:
            description += "\n\n❌ **AI Capabilities: Disabled** - Contact an administrator to enable AI features."
        
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Prompts(bot)) 