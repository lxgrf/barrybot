import requests
import json
from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext
import os
from dotenv import load_dotenv

load_dotenv()
discordKey = os.getenv("discord")
openaiKey = os.getenv("openai")
model = "gpt-3.5-turbo"
max_tokens = 200
temperature = 1.2
bot = Client(intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)
url = 'https://api.openai.com/v1/chat/completions'
headers = {'content-type': 'application/json', "Authorization":f"Bearer {openaiKey}"}

guilds ={
    "1010366904612954203":"a fantasy city", # Test Server
    "866376531995918346":"the city of Silverymoon, in Faerûn",
    "1001193835835183174":"the city of Caddocia, in a homebrew fantasy world",
         }

monitored_channels = {
    866376531995918346 : [880874308556169327,923399076609933312,880874380517855282,912466473639878666,880883916779696188,
                          912466154289774642,922542990185103411,922543035273867315,880897412401627166,880881928465682462,
                          939969226951757874,968247532176162816,987467362137702431,987474061590429806,987466872171683892,
                          987466023793995796,885219132595904613,907353116041699328,974155793928687616], # Silverymoon
    1114617197931790376 : [1150871698871156840,1172667577890259085], # TEST SERVER
}

def _server_error(ctx):
        title = "Error - Server not recognised."
        description = f"Your Server ID is {ctx.guild.id}. This server is not on the authorised list for this bot.\n\nPlease contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        return embed

@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.")
async def scene(ctx: SlashContext, character1, character2, request=""):
    await ctx.defer()
    description = ""
    if str(ctx.guild.id) not in guilds:
        embed = _server_error(ctx)
        await ctx.send(embed=embed)
    elif len(character1.split(" ")) < 5 or len(character2.split(" ")) < 5:
        description += "Ok, I'll be honest, I haven't read your scenes.\n\nCan you tell me a little more about these characters, to help me provide a detailed scene for you? For example, `Bob, a grumpy retired carpenter who misses his daughter` is much easier for me to work with than just `Bob`. I have done my best, but the scene I have generated may not fit your expectations.\n\n"
    
    title = "Here is your scene prompt!"
    city = guilds[str(ctx.guild.id)]
    description += f"**First character**: `{character1}`\n**Second character**: `{character2}`"
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
    description = ""
    if str(ctx.guild.id) not in guilds:
        embed = _server_error(ctx)
        await ctx.send(embed=embed)
    elif len(character.split(" ")) < 5:
        description += "Ok, I'll be honest, I haven't read your scenes.\n\nCan you tell me a little more about this character, to help me provide a detailed scene for you? For example, `Bob, a grumpy retired carpenter who misses his daughter` is much easier for me to work with than just `Bob`.\n\n"
        
    title = "Here is your solo scene prompt!"
    city = guilds[str(ctx.guild.id)]
    description += f"**Character**: `{character}`"
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

@slash.slash(name="lastmessage", description="Get the time of the last message in a channel.")
async def lastmessage(ctx: SlashContext):
    await ctx.defer()
    if ctx.guild.id not in monitored_channels:
        title = "Error - Server not recognised."
        description = f"Your Server ID is {ctx.guild.id}. This server is not on the authorised list for this bot.\n\nPlease contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed)
        return
    
    channel_list = monitored_channels[ctx.guild.id]
    description = ""
    active = []
    inactive = []

    for channel_id in channel_list:
        channel = bot.get_channel(int(channel_id))
        message = await channel.fetch_message(channel.last_message_id)
        messageTime = message.created_at
        timeElapsed = datetime.datetime.utcnow() - messageTime
        author = message.author
        status = ":green_circle:"
        if timeElapsed > datetime.timedelta(days=7):
            status = ":yellow_circle:"     
        if timeElapsed > datetime.timedelta(days=14):
            status = ":red_circle:"
        # format timeElapsed just as days
        if timeElapsed.days == 0:
            timeElapsed = "Today"
        else:
            timeElapsed = f"{timeElapsed.days} days ago"
        descString = f"{status} <#{channel_id}>: {messageTime.strftime('%d/%m/%Y')} by {author.display_name} ({timeElapsed})\n"

        if author.name == "Avrae":
            inactive.append(descString)
        else:
            active.append(descString)

    if len(active) > 0:
        description += "Active channels:\n"
        for line in active:
            description += line
        description += "\n"
    
    if len(inactive) > 0:
        description += "\nInactive channels:\n"
        for line in inactive:
            description += line

    embed = Embed(title="Last message", description=description)
    await ctx.send(embed=embed)
    return

bot.run(discordKey)
