import requests
import json
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
import os

openai_api = str(os.environ['openai'])
discord_api = str(os.environ['discord'])
bot = Client(intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)

url = 'https://api.openai.com/v1/completions'
headers = {'content-type': 'application/json', "Authorization":f'Bearer {openai_api}'}
footer = "/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene!"

@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail. Use natural language, and give as much or as little detail as you want.")
async def scene(ctx: SlashContext, character1, character2, request=""):
    await ctx.defer()
    description = f"**First character**: `{character1}`\n**Second character**: `{character2}`"
    prompt = f"Give a brief idea for a low-stakes encounter, a roleplay scene between two D&D characters in the city of Silverymoon, in Faerûn. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. The characters have not interacted before this scene. Describe the inciting incident only, and not what happens next."
    if request != "": 
        prompt += f" {request}."
        description += f"\n**Request**: `{request}`"
    # payload = {"model":"text-davinci-003","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = {"model":"gpt-3.5-turbo","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = json.dumps(payload, indent = 4)
    r = requests.post(url=url, data=payload, headers=headers)
    description += f"\n\n{r.json()['choices'][0]['text']}"
    embed = Embed(title=f"Here is your scene prompt!", description=description)
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

@slash.slash(name="solo", description="Get a solo scene prompt! Describe the character involved specifying any relevant detail. Use natural language, and give as much or as little detail as you want.")
async def scene(ctx: SlashContext, character1, detail=""):
    await ctx.defer()
    description = f"**Solo character**: `{character1}`"
    prompt = f"Give a brief idea for a creative writing exercise from the perspective of {character1}, a D&D character in the city of Silverymoon, in Faerûn. Set up an emotionally resonant scene, and describe the inciting incident only, and not what happens next."
    if detail != "": 
        prompt += f" Information on the character: {detail}."
        description += f"\n**Specified detail**: `{detail}`"
    # payload = {"model":"text-davinci-003","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = {"model":"gpt-3.5-turbo","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = json.dumps(payload, indent = 4)
    r = requests.post(url=url, data=payload, headers=headers)
    description += f"\n\n{r.json()['choices'][0]['text']}"
    embed = Embed(title=f"Here is your solo scene prompt!", description=description)
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

bot.run(discord_api)