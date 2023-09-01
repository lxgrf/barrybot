import requests
import json
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
import os

openai_api = str(os.environ['openai'])
discord_api = str(os.environ['discord'])
# model = "text-davinci-003"
model = "gpt-3.5-turbo"
max_tokens = 200
temperature = 1.2

bot = Client(intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)

# url = 'https://api.openai.com/v1/completions'
url = 'https://api.openai.com/v1/chat/completions'
headers = {'content-type': 'application/json', "Authorization":f'Bearer {openai_api}'}
footer = f"/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."

@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.")
async def scene(ctx: SlashContext, character1, character2, request=""):
    await ctx.defer()
    description = f"**First character**: `{character1}`\n**Second character**: `{character2}`"
    prompt = f"Give a concise bullet-point summary of an idea for a low-stakes encounter, for a roleplay scene between two D&D characters in the city of Silverymoon, in Faerûn. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than five bullet points."
    if request != "": 
        prompt += f" {request}."
        description += f"\n**Request**: `{request}`"
    messages = [
        {"role": "system", "content": "You are a D&D Dungeonmaster."},
        {"role": "user", "content":prompt},
    ]
    # payload = {"model":"text-davinci-003","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = {
        "model":model,
        "messages":messages,
        "temperature":temperature,
        "max_tokens":max_tokens}
    payload = json.dumps(payload, indent = 4)
    r = requests.post(url=url, data=payload, headers=headers)
    description += f"\n\n{r.json()['choices'][0]['message']['content']}"
    embed = Embed(title=f"Here is your scene prompt!", description=description)
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

@slash.slash(name="solo", description="Get a solo prompt! Describe the character involved specifying any relevant detail.")
async def solo(ctx: SlashContext, character, request=""):
    await ctx.defer()
    description = f"**Character**: `{character}`"
    prompt = f"Give a concise bullet-point summary of an idea for an emotive and interesting character development scene for a D&D character in the city of Silverymoon, in Faerûn. The character is {character}. Avoid creating backstory for this character, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than 5 bullet points."
    if request != "": 
        prompt += f" {request}."
        description += f"\n**Request**: `{request}`"
    messages = [
        {"role": "system", "content": "You are a D&D Dungeonmaster."},
        {"role": "user", "content":prompt},
        ]
    # payload = {"model":"text-davinci-003","prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = {
        "model":model,
        "messages":messages,
        "temperature":temperature,
        "max_tokens":max_tokens}
    # payload = {"model":"text-davinci-003","prompt":prompt,"temperature":0.8,"max_tokens":150}
    # payload = {"model":model,"prompt":prompt,"temperature":0.8,"max_tokens":150}
    payload = json.dumps(payload, indent = 4)
    r = requests.post(url=url, data=payload, headers=headers)
    description += f"\n\n{r.json()['choices'][0]['message']['content']}"
    embed = Embed(title=f"Here is your solo prompt!", description=description)
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

@slash.slash(name="help", description="Get help with the bot.")
async def help(ctx: SlashContext):  
    await ctx.defer()
    title = "AI Suggestions Help"
    description = "This bot generates scene ideas based on brief character descriptions you supply. It uses the OpenAI API to generate text, and the Discord API to send it to you. The bot is currently in beta, so please report any bugs to the developer, @lxgrf."
    description += f"\n\nThe bot is currently using the {model} model."
    embed = Embed(title=title, description=description)
    await ctx.send(embed=embed)

bot.run(discord_api)