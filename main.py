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

@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.")
async def scene(ctx: SlashContext, character1, character2, request=""):
    await ctx.defer()
    description = f"**First character**: `{character1}`\n**Second character**: `{character2}`"
    prompt = f"Give a concise bullet-point summary of an idea for a low-stakes encounter, for a roleplay scene between two D&D characters in the city of Silverymoon, in Faerûn. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than four bullet points."
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
    footer = f"/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

@slash.slash(name="solo", description="Get a solo prompt! Describe the character involved specifying any relevant detail.")
async def solo(ctx: SlashContext, character, request=""):
    await ctx.defer()
    description = f"**Character**: `{character}`"
    prompt = f"Give a short, concise, bullet-point summary of an idea for an emotive and interesting character development scene for a D&D character in the city of Silverymoon, in Faerûn. The character is {character}. Avoid creating backstory for this character, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than 3 bullet points."
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
    footer = f"/solo | Request your own solo scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with {model}."
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)

@slash.slash(name="help", description="Get help with the bot.")
async def help(ctx: SlashContext):  
    await ctx.defer()
    title = "AI Suggestions Help"
    description = "This bot generates scene ideas based on brief character descriptions you supply. It uses the OpenAI API to generate text, and the Discord API to send it to you."
    # description += "\n\nThe bot does not _know_ your character, so be sure to include any relevant detail in your description. For example, `character:Dave` will not produce results as good as `character:Dave, a retired carpenter with terrible luck, who has recently had an argument with his daughter`."
    description += "\nNote that any detail supplied may be used, so if you don't want the scene to, for example, focus on stealing something, don't mention that they are a thief - even if they are."
    description += "\n\n## Commands"
    description += "\n`/scene` - Get a scene prompt! Describe the characters involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
    description += "\n`/solo` - Get a solo prompt! Describe the character involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
    description += "\n\n## Example Usage"
    description += "\n\n ### Bad Usage:\n `/scene character1:Dave, character2:Geraldine`\n It might be clear to you who Dave and Geraldine are, but the bot doesn't know. It will do its best, but will generate a prompt that may not fit your expectations."
    description += "\n\n ### Good Usage:\n `scene character1:Dave, a retired carpenter who wants to reconcile with his estranged daughter but is too proud to admit fault, character 2:Geraldine, Dave's daughter, who is a successful merchant and has no time for her father's nonsense`\n This description is much more detailed, and the bot will be able to generate a prompt that fits your expectations."
    description += f"\n\nThe bot is currently in beta, using the {model} model, so please report any bugs or suggestions to @lxgrf."
    embed = Embed(title=title, description=description)
    await ctx.send(embed=embed)

bot.run(discord_api)