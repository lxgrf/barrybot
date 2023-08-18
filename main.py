import requests
import json
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
# from boto.s3.connection import S3Connection
import os

openai_api = os.environ['openai']
discord_api = os.environ['discord']
# s3 = S3Connection(os.environ['S3_KEY'], os.environ['S3_SECRET'])
bot = Client(intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)

url = 'https://api.openai.com/v1/completions'
headers = {'content-type': 'application/json', "Authorization":f'Bearer {openai_api}'}
footer = "/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene!"

@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.")
async def scene(ctx: SlashContext, character1, character2, request=""):
    await ctx.defer()
    description = f"**First character**: `{character1}`\n**Second character**: `{character2}`"
    prompt = f"Give a brief idea for a low-stakes encounter, for a roleplay scene between two D&D characters in the city of Silverymoon, in Faerûn. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. The characters have not interacted before this scene. Describe the setup only, the players will decide how it proceeds."
    if request != "": 
        prompt += f" {request}."
        description += f"\n**Request**: `{request}`"
    payload = {"model":"text-davinci-003","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = json.dumps(payload, indent = 4)
    r = requests.post(url=url, data=payload, headers=headers)
    description += f"\n\n{r.json()['choices'][0]['text']}"
    embed = Embed(title=f"Here is your scene prompt!", description=description)
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

bot.run(discord_api)