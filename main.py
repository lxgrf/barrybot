import requests
import json
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
import os

model = "gpt-3.5-turbo"
max_tokens = 200
temperature = 1.2
bot = Client(intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)
url = 'https://api.openai.com/v1/chat/completions'
headers = {'content-type': 'application/json', "Authorization":f"Bearer {str(os.environ['openai'])}"}

guilds ={
    "1010366904612954203":"a fantasy city", # Test Server
    "866376531995918346":"the city of Silverymoon, in Faerûn",
    "1001193835835183174":"the city of Caddocia, in a homebrew fantasy world",
         }

def _server_error(ctx):
        title = "Error - Server not recognised."
        description = f"Your Server ID is {ctx.guild.id}. This server is not on the authorised list for this bot.\n\nPlease contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        return embed

@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.")
async def scene(ctx: SlashContext, character1, character2, request=""):
    await ctx.defer()
    if str(ctx.guild.id) not in guilds:
        embed = _server_error(ctx)
        await ctx.send(embed=embed)
    elif len(character1.split(" ")) < 3 or len(character2.split(" ")) < 3:
        title = "Please provide more detail."
        description = "Ok, I'll be honest, I haven't read your scenes.\n\nCan you tell me a little more about these characters, to help me provide a detailed scene for you? For example, `Bob, a grumpy retired carpenter who misses his daughter` is much easier for me to work with than just `Bob`."
        footer = f"/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."
        embed = Embed(title=title, description=description, footer=footer)
        await ctx.send(embed=embed)
    else:
        title = "Here is your scene prompt!"
        city = guilds[str(ctx.guild.id)]
        description = f"**First character**: `{character1}`\n**Second character**: `{character2}`"
        prompt = f"Give a concise bullet-point summary of an idea for a low-stakes encounter, for a roleplay scene between two D&D characters in {city}. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than four bullet points."
        if request != "": 
            prompt += f" {request}."
            description += f"\n**Request**: `{request}`"
        messages = [{"role": "system", "content": "You are a D&D Dungeonmaster."},{"role": "user", "content":prompt},]
        payload = {"model":model,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
        payload = json.dumps(payload, indent = 4)
        r = requests.post(url=url, data=payload, headers=headers)
        description += f"\n\n{r.json()['choices'][0]['message']['content']}"
        footer = f"/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."
        embed = Embed(title=title, description=description, footer=footer)
        await ctx.send(embed=embed)

@slash.slash(name="solo", description="Get a solo prompt! Describe the character involved specifying any relevant detail.")
async def solo(ctx: SlashContext, character, request=""):
    await ctx.defer()
    if str(ctx.guild.id) not in guilds:
        embed = _server_error(ctx)
        await ctx.send(embed=embed)
    elif len(character.split(" ")) < 3:
        title = "Please provide more detail."
        description = "Ok, I'll be honest, I haven't read your scenes.\n\nCan you tell me a little more about these characters, to help me provide a detailed scene for you? For example, `Bob, a grumpy retired carpenter who misses his daughter` is much easier for me to work with than just `Bob`."
        footer = f"/solo | Request your own solo scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."
        embed = Embed(title=title, description=description, footer=footer)
        await ctx.send(embed=embed)
    else:
        title = "Here is your solo scene prompt!"
        city = guilds[str(ctx.guild.id)]
        description = f"**Character**: `{character}`"
        prompt = f"Give a short, concise, bullet-point summary of an idea for an emotive and interesting character development scene for a D&D character in {city}. The character is {character}. Avoid creating backstory for this character, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than 3 bullet points."
        if request != "": 
            prompt += f" {request}."
            description += f"\n**Request**: `{request}`"
        messages = [{"role": "system", "content": "You are a D&D Dungeonmaster."},{"role": "user", "content":prompt},]
        payload = {"model":model,"messages":messages,"temperature":temperature,"max_tokens":max_tokens}
        payload = json.dumps(payload, indent = 4)
        r = requests.post(url=url, data=payload, headers=headers)
        description += f"\n\n{r.json()['choices'][0]['message']['content']}"
        footer = f"/solo | Request your own solo scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."
        embed = Embed(title=title, description=description, footer=footer)
        await ctx.send(embed=embed)

@slash.slash(name="help", description="Get help with the Scene Prompt bot.")
async def help(ctx: SlashContext):  
    await ctx.defer()
    title = "AI Suggestions Help"
    description = "This bot generates scene ideas based on brief character descriptions you supply. It uses the OpenAI API to generate text, and the Discord API to send it to you."
    description += "\nNote that any detail supplied may be used, so mentioning that your character is a thief ups the chances of the scene involving theft. Hold back detail you don't want to see."
    description += "\n\n## Commands"
    description += "\n`/scene` - Get a scene prompt! Describe the characters involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
    description += "\n`/solo` - Get a solo prompt! Describe the character involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
    description += "\n\n## Example Usage"
    description += "\n\n**Bad Usage**:\n `/scene character1:Dave, character2:Geraldine`\n It might be clear to you who Dave and Geraldine are, but the bot doesn't know. It will do its best, but will generate a prompt that may not fit your expectations."
    description += "\n\n**Good Usage**:\n `/scene character1:Dave, a retired carpenter who wants to reconcile with his estranged daughter but is too proud to admit fault, character 2:Geraldine, Dave's daughter, who is a successful merchant and has no time for her father's nonsense`\n This description is much more detailed, and the bot will be able to generate a prompt that fits your expectations."
    description += f"\n\nThe bot is currently in beta, using the {model} model, so please report any bugs or suggestions to @lxgrf. \n\n`Guild ID: {ctx.guild.id}`"
    embed = Embed(title=title, description=description)
    await ctx.send(embed=embed)

bot.run(str(os.environ['discord']))
