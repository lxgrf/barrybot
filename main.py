from discord import Client, Intents, Embed
from discord_slash import SlashCommand, SlashContext

import datetime
import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

anthro = anthropic.Anthropic(
    api_key = os.getenv("anthropic")
)

bot = Client(intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True)

guilds ={
    "1010366904612954203":"a fantasy city", # Test Server
    "866376531995918346":"the city of Silverymoon, in Faerûn",
    "1001193835835183174":"the city of Caddocia, in a homebrew fantasy world",
         }

# User filtering
include_role = "Member"
exclude_role = "Inactive"
inactivity_threshold = 31 # days
warning_threshold = 14 # days

authorised_roles = ["Helper","Dragonspeaker","Mods","Admin","Owner"]

opt_in_roles = {
    866376531995918346 : "AI Scene Summary Permission", # Silverymoon
    1001193835835183174: "AI Approval", # Caddocia
    1114617197931790376: "Owner", # Test Server
}

monitored_channels = {
    866376531995918346 : [ # Silverymoon
                        880874308556169327,923399076609933312,880874380517855282,912466473639878666,880883916779696188,
                        912466154289774642,922542990185103411,922543035273867315,880897412401627166,880881928465682462,
                        939969226951757874,968247532176162816,987467362137702431,987474061590429806,987466872171683892,
                        987466023793995796,885219132595904613,907353116041699328,974155793928687616,880874502240751636,
                        987466462383980574,880874331247349810,944396675647168532,922534449252556820,923398707104346112,
                        968247884992618516,990096024171323464,987466249107816528,880889305881534475,923400219427758151,
                        880877522500341802,939969468740804659,987465629818847304,987473574271004682,885219090883571742,
                        907352356226736128,974155308895186984,880874583840931890,939970472462921808,968247977510576240,
                        880874392316420117,885377822426791966,880885934793588786,880889751400513576,923400462013693972,
                        930648938938257439,987465378257072148,923401112097284177,992147947028496404,880893508456681474,
                        930648696935288922,885219048772735017,907352384341151845,974156178089189386,880891131779481631,
                        930647613085200504,880891175874232320,880891889841225768,992148025982079087,
                        968177303387504680,987464710137983067,905908992558104636,930647843172147281
                          ],
    1114617197931790376 : [ # Test Server
                        1150871698871156840,1172667577890259085,1121682493242880052,1114617198430916610,1117684731958530099
                          ], 
    1001193835835183174 : [ # Caddocia
                        1121436212557783080,1003048340826624091,1001197651397726208,1001197934416773152,1001197786726936667,
                        1001197861855309915,1001198127149240350,1001198170505752688,1121436272381153310,1001199222567223499,
                        1001199312610525246,1001199501886881892,1001199540533198889,1001199563211821198,1001495054331940974,
                        1001201017196658758,1121436358066585691,1001200354786021436,1001200373631033514,1001200448813936680,
                        1001200474332070058,1001200675763531786,1001200882316214282,1001200804578996344,1001201142610526278,
                        1001201170238414988,1001495089060794558,1001201287947366461,1121436436411981855,1001201422244782110,
                        1001201480981807205,1001201480981807205,1001201556814839858,1001201646556164218,1001201854039986297,
                        1001201929080275104,1001201953772163252,1001201998626029590,1001202047409995968,1001202085112594622,
                        1001495122615222362,1001202340851880016,1121436502388375664,1001202447739535460,1001202518979788800,
                        1001202475510022224,1001202553859621004,1001202634251841556,1001203000674623578,1001202966474281000,
                        1001203929394196510,1001203929394196510,1001203999384555590,1001204017466187916,1001204049875587123,
                        1001204076714917981,1001213810629165117,1001491476905209908,1001495152990363698,1001203417835905074,
                        1050399592287584276,1050399755336962078,1050399912698843186,1044715490544734278,1044717853754019890,
                        1044715531430797372,
                        ],
            }
    
tldr_excluded_channels = {
    866376531995918346:[], #Silverymoon
    1114617197931790376: [], #Test Server
    1001193835835183174: [1044715490544734278,1044717853754019890,1044715531430797372], #Caddocia
}

tldr_additional_channels = {
    866376531995918346:[923663727394443284,990336609192906822,926378655091945482,1079463185712697464,1158841934345945248,990765159687532554,
                        990320570233159740,929174188651085824,1039271164696084550,1023774505006542919,928093443706724352,928093568424349717,
                        928120536859557928,1084512254147448902,948024606512521297], #Silverymoon
    1114617197931790376: [], #Test Server
    1001193835835183174: [1087062242056474765,1034466115037962311,1115703983256899615,1185359232229453834,922383749281382400,1090358867797475348,], #Caddocia
}

tldr_output_channels = {
    866376531995918346: 1031234608458641408, #Silverymoon
    1114617197931790376: 0, #Test Server
    1001193835835183174: 1237521328244789299, #Caddocia
}

channeltimes = {
    866376531995918346 : {"yellow":7,"red":14}, # Silverymoon
    1001193835835183174: {"yellow":14,"red":31}, # Caddocia
    1114617197931790376: {"yellow":14,"red":31}, # Test Server
}

def _server_error(ctx):
    title = "Error - Server not recognised."
    description = f"Your Server ID is {ctx.guild.id}. This server is not on the authorised list for this bot.\n\nPlease contact `@lxgrf` if you believe this is in error."
    embed = Embed(title=title, description=description)
    return embed

def _authorised_user():
    title = "Error - User not authorised."
    description = "Some functions are restricted to authorised users only. Please contact `@lxgrf` if you feel you should have access."
    embed = Embed(title=title, description=description)
    return embed

def claude_call(prompt, max_tokens=200, temperature=0.8):
    message = anthro.messages.create(
        # model="claude-3-opus-20240229",
        model = "claude-3-sonnet-20240229",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    return message.content[0].text

def mistral_call(prompt, max_tokens=200, temperature=0.8):
    response = mistral.chat(
        model= "mistral-large-latest",
        messages=[ChatMessage(role="user", content=prompt)],
        temperature=temperature,
        max_tokens=max_tokens,
        )
    return response.choices[0].message.content


@slash.slash(name="scene", description="Get a scene prompt! Describe the characters involved specifying any relevant detail.",
             options=[discord_slash.manage_commands.create_option(name="first_character", description="Details of the first character in the scene - the more the better", option_type=3, required=True),
                      discord_slash.manage_commands.create_option(name="second_character", description="Details of the second character in the scene - the more the better", option_type=3, required=True),
                      discord_slash.manage_commands.create_option(name="request", description="Any specific requests for the scene prompt.", option_type=3, required=False)])
async def scene(ctx: SlashContext,character1,character2,request):
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
    prompt = f"You are a D&D Dungeonmaster. Give a concise bullet-point summary of an idea for a low-stakes encounter, for a roleplay scene between two D&D characters in {city}. The first character is {character1}, and the second character is {character2}. Avoid creating backstory for these characters, as they are pre-existing. Describe the initial inciting incident only, and not what happens next. No more than four bullet points."
    if request != "": 
        prompt += f" {request}."
        description += f"\n**Request**: `{request}`"
    
    description += f"\n\n{claude_call(prompt)}"

    footer = f"/scene | Request your own scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with Anthropic Claude."
    embed = Embed(title=title, description=description, footer=footer)
    await ctx.send(embed=embed)

@slash.slash(name="solo", description="Get a solo prompt! Describe the character involved specifying any relevant detail.",
             options=[discord_slash.manage_commands.create_option(name="character", description="Details of a character in the scene - the more the better", option_type=3, required=True),
                      discord_slash.manage_commands.create_option(name="request", description="Any specific requests for the scene prompt.", option_type=3, required=False)])
async def solo(ctx: SlashContext,character,request):
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

    description += f"\n\n{claude_call(prompt)}"
    footer = f"/solo | Request your own solo scene prompt! Prompts are AI-generated, so feel free to change or ignore any detail. It's your scene! Generated with Anthropic's Claude AI."
    embed = Embed(title=title, description=description, footer=footer)
    await ctx.send(embed=embed)

@slash.slash(name="help", description="Get help with the Scene Prompt bot.")
async def help(ctx: SlashContext):  
    await ctx.defer()
    title = "AI Suggestions Help"
    description = "This bot generates scene ideas based on brief character descriptions you supply. It uses the Anthropic Claude API to generate text, and the Discord API to send it to you."
    description += "\nNote that any detail supplied may be used, so mentioning that your character is a thief ups the chances of the scene involving theft. Hold back detail you don't want to see."
    description += "\n\n## Commands"
    description += "\n`/scene` - Get a scene prompt! Describe the characters involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
    description += "\n`/solo` - Get a solo prompt! Describe the character involved specifying any relevant detail. Add a request to the end of your description to get a prompt with a specific focus - something you want to come up, or _not_ come up, or a specific setting, etc."
    description += "\n\n## Example Usage"
    description += "\n\n**Bad Usage**:\n `/scene character1:Dave, character2:Geraldine`\n It might be clear to you who Dave and Geraldine are, but the bot doesn't know. It will do its best, but will generate a prompt that may not fit your expectations."
    description += "\n\n**Good Usage**:\n `/scene character1:Dave, a retired carpenter who wants to reconcile with his estranged daughter but is too proud to admit fault, character 2:Geraldine, Dave's daughter, who is a successful merchant and has no time for her father's nonsense`\n This description is much more detailed, and the bot will be able to generate a prompt that fits your expectations."
    description += f"\n\nThe bot is currently in beta, using Anthropic's Claudea, so please report any bugs or suggestions to @lxgrf. \n\n`Guild ID: {ctx.guild.id}`"
    embed = Embed(title=title, description=description)
    await ctx.send(embed=embed)

@slash.slash(name="useractivity", description="See the RP activity of users.")
async def useractivity(ctx: SlashContext):
    await ctx.defer()
    if ctx.guild.id not in monitored_channels.keys():
        title = "Error - Server not recognised."
        description = f"Your Server ID is {ctx.guild.id}. This server is not on the authorised list for this bot.\n\nPlease contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed)
        return

    # see if user is authorised - if any of the authorised roles are in the user's roles, they are authorised
    authorised = False
    for role in ctx.author.roles:
        if role.name in authorised_roles:
            authorised = True
    if not authorised:
        embed = _authorised_user()
        await ctx.send(embed=embed)
        return

    # get all users 
    active = [user.id for user in ctx.guild.members if include_role in [role.name for role in user.roles] and exclude_role not in [role.name for role in user.roles]]

    # Get utc time for one month prior to now
    one_month_ago = datetime.datetime.utcnow() - datetime.timedelta(days=inactivity_threshold)
    fourteen_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=warning_threshold)
    # Get message histories for each channel
    channel_histories_new = {}
    channel_histories_old = {}
    for channel_id in monitored_channels[ctx.guild.id]:
        channel = bot.get_channel(int(channel_id))
        old_messages = channel.history(limit=50, after=one_month_ago, before=fourteen_days_ago)
        new_messages = channel.history(limit=50, after=fourteen_days_ago)
        channel_histories_new[channel_id] = new_messages
        channel_histories_old[channel_id] = old_messages

    # Work through each message history and count messages by active users
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

    # Sort the user activity by number of messages
    new_activity = {k: v for k, v in sorted(new_activity.items(), key=lambda item: item[1], reverse=False)}
    total_activity = {k: v for k, v in sorted(total_activity.items(), key=lambda item: item[1], reverse=False)}
    
    description = ""
    inactive = {}
    # if any users have zero posts
    if 0 in total_activity.values():
        description = f":red_circle: No posts in the last {inactivity_threshold} days:\n"
        # add each user with zero posts to the description
        for user, posts in total_activity.items():
            if posts == 0:
                description += f"<@{user}>: {total_activity[user]}\n"
                inactive.update({user: 200})
        description += "\n"

    # if any users have zero posts in the last 14 days, but some in the last 31
    if 0 in new_activity.values():
        description += f":orange_circle: No posts in the last {warning_threshold} days:\n"
        # add each user with zero posts to the description
        for user, posts in new_activity.items():
            if posts == 0 and total_activity[user] > 0:
                description += f"<@{user}>: {new_activity[user]}\n"
        description += "\n"

    # if any users have 1-3 posts
    if 1 in total_activity.values() or 2 in total_activity.values() or 3 in total_activity.values():
        description += f":yellow_circle: 1-3 posts in the last {inactivity_threshold} days:\n"
        # add each user with 1-3 posts to the description
        for user, posts in total_activity.items():
            if 1 <= posts <= 3:
                description += f"<@{user}>: {total_activity[user]}\n"
        description += "\n"
    
    # Everyone else
    description += f":green_circle: 4+ posts in the last {inactivity_threshold} days:\n"
    # add each user with 4+ posts to the description
    for user, posts in total_activity.items():
        if posts >= 4:
            description += f"<@{user}>: {total_activity[user]}\n"

    embed = Embed(title="User Activity in RP Channels", description=description)
    await ctx.send(embed=embed)

    # Now let's dig deeper into the inactive users and when they did last post
    description = ""
    # get all messages from the last 180 days
    six_months_ago = datetime.datetime.utcnow() - datetime.timedelta(days=180)

    for channel_id in monitored_channels[ctx.guild.id]:
        channel = bot.get_channel(int(channel_id))
        messages = channel.history(limit=500, after=six_months_ago, before=one_month_ago)
        async for message in messages:
            if message.author.id in inactive.keys():
                # convert message.created_at to days since today
                timeElapsed = datetime.datetime.utcnow() - message.created_at
                if timeElapsed.days < inactive[message.author.id]:
                    inactive[message.author.id] = int(timeElapsed.days)

    # Remove users who have not posted at all to a separate list
    inactive_zero = {}
    for user, days in inactive.items():
        if days == 200:
            inactive_zero.update({user: days})
    for user in inactive_zero.keys():
        inactive.pop(user)

    # if any users have zero posts
    if len(inactive_zero) > 0:
        description += "No RP posts in the last 180 days. Please note that this may include brand new users who have yet to post.\n\n"
        for user, days in inactive_zero.items():
            description += f"<@{user}>\n"

    if len(inactive) > 0:
        description += "\nPosts in the past, but none in the last 31 days:\n\n"
        for user, days in sorted(inactive.items(), key=lambda item: item[1], reverse=True):
            description += f"<@{user}>: last post {days} days ago.\n"

    if len(inactive_zero) > 0 or len(inactive) > 0:
        embed = Embed(title="Inactive User Deep Dive", description=description)
        await ctx.send(embed=embed)

    return

@slash.slash(name="channelactivity", description="Get the time of the last message in a channel.")
async def channelactivity(ctx: SlashContext):
    await ctx.defer()
    if ctx.guild.id not in monitored_channels.keys():
        title = "Error - Server not recognised."
        description = f"Your Server ID is {ctx.guild.id}. This server is not on the authorised list for this bot.\n\nPlease contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed)
        return
    
    authorised = False
    for role in ctx.author.roles:
        if role.name in authorised_roles:
            authorised = True
    if not authorised:
        embed = _authorised_user()
        await ctx.send(embed=embed)
        return
    
    channel_list = monitored_channels[ctx.guild.id]
    description = ""
    active = []
    inactive = []
    stale = []

    for channel_id in channel_list:
        channel = bot.get_channel(int(channel_id))
        messages = channel.history(limit=1)
        message = await messages.next()
        messageTime = message.created_at
        timeElapsed = datetime.datetime.utcnow() - messageTime
        author = message.author
        status = ":green_circle:"
        if timeElapsed > datetime.timedelta(days=channeltimes[ctx.guild.id]["yellow"]):
            status = ":yellow_circle:"     
        if timeElapsed > datetime.timedelta(days=channeltimes[ctx.guild.id]["red"]):
            status = ":red_circle:"
            if message.author.name != "Avrae":
                stale.append(channel_id)
        # format timeElapsed just as days
        if timeElapsed.days == 0:
            timeElapsed = "Today"
        else:
            timeElapsed = f"{timeElapsed.days} days ago"
        descString = f"{status} <#{channel_id}>: {messageTime.strftime('%d/%m/%Y')} ({timeElapsed})\n"

        if author.name == "Avrae":
            inactive.append(descString)
        else:
            active.append(descString)

    if len(active) > 0:
        description = "# Active channels:\n(Channels with an ongoing RP scene)\n\n"
        for line in active:
            description += line
        description += "\n"
        embed = Embed(title="Last message", description=description)
        await ctx.send(embed=embed)


    # Now let's delve into the long-standing stale channels
    # For the Channels in the stale list, get the time of the last post by Avrae, and then a list of users who have posted since then

    if len(stale) > 0:
        description = "Copy and past the below for your weekly pinging needs\n\n"
        description += "```\n## Weekly pings!\nAs usual, this is a friendly check in on those scenes which seem to be slowing down. How's it going? How's life? Are you both communicating and happy with the pace of things? Do you need any help or hand from anyone?\n"
        stalepoint = datetime.datetime.utcnow() - datetime.timedelta(days=channeltimes[ctx.guild.id]["red"])
        further_back = datetime.datetime.utcnow() - datetime.timedelta(days=channeltimes[ctx.guild.id]["red"]*6)
        

        for channel_id in stale:
            users = []
            channel = bot.get_channel(int(channel_id))
            message_history = channel.history(limit=25, before=stalepoint, after=further_back)
            async for message in message_history:
                if message.author.name == "Avrae":
                    break
                elif message.author.id not in users:
                    users.append(message.author.id)
            users = [f"<@{user}>" for user in users]
            users = ", ".join(users)
            description += f"<#{channel_id}>: ({users})\n"
        description += "```"
        embed = Embed(title="Ping Post", description=description)
        await ctx.send(embed=embed)
    return

@slash.slash(name="tldr",description="Summarise the scene above. Requires all scene contributors to have opted in to this functionality. If you want to summarise an older scene, get the message IDs of the start and end points, and supply them as the optional arguments.",
             options=[discord_slash.manage_commands.create_option(name="scenetitle", description="Title for the scene, if preferred", option_type=3, required=False),
                      discord_slash.manage_commands.create_option(name="startmessageid", description="Message ID of the start of the scene", option_type=3, required=False),
                      discord_slash.manage_commands.create_option(name="endmessageid", description="Message ID of the end of the scene", option_type=3, required=False)])
async def tldr(ctx: SlashContext, scenetitle, startmessageid, endmessageid):
    await ctx.defer(hidden=True)
    if str(ctx.guild.id) not in guilds:
        embed = _server_error(ctx)
        await ctx.send(embed=embed,hidden=True)
        return

    elif ctx.channel.id not in monitored_channels[ctx.guild.id] and ctx.channel.id not in tldr_additional_channels[ctx.guild.id]:
        title = "Error - Channel not monitored."
        description = f"This channel is not monitored for RP activity. Please contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed,hidden=True)
        return

    elif ctx.channel.id in tldr_excluded_channels[ctx.guild.id]:
        title = "Error - Channel excluded."
        description = f"This channel is excluded from TL;DR summaries. Please contact `@lxgrf` if you believe this is in error."
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed,hidden=True)
        return

    # Get channel messages since the most recent Avrae message.
    # If the last message was from Avrae, ignore it.
    # If there are no messages from Avrae, go back to the start of the channel
    # If there are no messages at all, say so.
    channel = bot.get_channel(ctx.channel.id)
    messages = [message async for message in channel.history(limit=1)]
    if len(messages) == 0:
        description = "No messages in this channel."
        embed = Embed(title="TL;DR", description=description)
        await ctx.send(embed=embed, hidden=True)
        return
    new_messages = []

    if not (startmessageid or endmessageid):
        messages = [message async for message in channel.history(limit=200)]
        messages = messages[::-1]
        # If the last message is from Avrae, remove it
        if messages[-1].author.name == "Avrae":
            messages.pop()

        # Find the most recent message from Avrae, and remove all messages before it
        for i in range(len(messages)):
            if messages[i].author.name == "Avrae":
                new_messages = messages[i:]
        if len(new_messages) != 0:
            messages = new_messages

    elif not (startmessageid and endmessageid):
        description = "If no message IDs are provided, the bot will attempt to summarise the most recent scene in this channel. If _both_ are provided, the bot will attempt to summarise the scene in between them.\n\nNot sure what to do with only one message ID."
        embed = Embed(title="TL;DR", description=description)
        await ctx.send(embed=embed, hidden=True)
        return


    else:
        try:
            startmessageid = int(startmessageid)
            endmessageid = int(endmessageid)
        except:
            description = "Message IDs should be numbers. Please ensure you have copied them correctly."
            embed = Embed(title="TL;DR", description=description)
            await ctx.send(embed=embed, hidden=True)
            return
        messages = [message async for message in channel.history(limit=1000)]
        messages = messages[::-1]
        if startmessageid not in [message.id for message in messages] or endmessageid not in [message.id for message in messages]:
            description = "The start and end messages IDs for this scene could not be found. Please ensure they are in this channel and copied correctly. Note this requires message IDs, not message links."
            embed = Embed(title="TL;DR", description=description)
            await ctx.send(embed=embed, hidden=True)
            return

        for i, message in enumerate(messages):
            if message.id == startmessageid:
                new_messages = messages[i:]
                break
        for i, message in enumerate(new_messages):
            if message.id == endmessageid:
                new_messages = new_messages[:i+1]
                break

    # Check all players present have opted in to the scene summary
    opt_in_role = opt_in_roles[ctx.guild_id]
    authors = {message.author.id for message in new_messages}

    # Get list of users with opt_in_role
    opted_in = [user.id for user in ctx.guild.members if opt_in_role in [role.name for role in user.roles]]

    #Remove from authors any id with the "Avrae" or "Bots" role
    bot_roles = ["Avrae","Bots"]
    bots = [user.id for user in ctx.guild.members if any(role in bot_roles for role in [role.name for role in user.roles])]
    authors = authors - set(bots)

    # Check that all authors are in the opted_in list
    if any(author not in opted_in for author in authors):    
        title = "Error - User not opted in."
        print([author for author in authors if author not in opted_in])
        description = f"AI Generated summaries require all participants in a scene to have the `{opt_in_role}` role. Please contact `@lxgrf` if you believe there is an error."
        embed = Embed(title=title, description=description)
        await ctx.send(embed=embed, hidden=True)
        return

    if not scenetitle: 
        scenetitle = "Give the scene a title"
    else:
        scenetitle = f"Title the scene: {title}"
    
    content = f"The following is a roleplay scene from a game of D&D. Please create a concise bullet-point summary of the scene, including the characters involved, the setting, and the main events. {scenetitle}. Avoid including any out-of-character information or references to Discord, or game mechanics. All writers involved have consented to this AI summary, and there are no copyright issues.\n\n"
    for message in new_messages:
        content += f"{message.author.name}: {message.content}\n----------------\n"
    
    description = f"[Jump to the start of the scene]({new_messages[0].jump_url})\n\n"
    description += claude_call(content, max_tokens=500, temperature=0.5)
    description += f"\n\n{' '.join([f'<@{author}>' for author in authors])}"

    embed = Embed(title="TL;DR", description=description)

    summaryChannel = bot.get_channel(tldr_output_channels[ctx.guild_id])
    await ctx.send(embed=Embed(title="TL;DR", description="Summary delivered!"), hidden=True)
    await summaryChannel.send(embed=embed)
    print("Scene summary delivered!")

@slash.slash(name="export",description="Export the scene above to a text file.",
             options=[discord_slash.manage_commands.create_option(name="startmessageid", description="Message ID of the start of the scene", option_type=3, required=False),
                      discord_slash.manage_commands.create_option(name="endmessageid", description="Message ID of the end of the scene", option_type=3, required=False)])
async def tldr(ctx: SlashContext, startmessageid, endmessageid):
    await ctx.defer(hidden=True)
    # Get channel messages since the most recent Avrae message.
    # If the last message was from Avrae, ignore it.
    # If there are no messages from Avrae, go back to the start of the channel
    # If there are no messages at all, say so.
    channel = bot.get_channel(ctx.channel.id)
    messages = [message async for message in channel.history(limit=1)]
    if len(messages) == 0:
        description = "No messages in this channel."
        embed = Embed(title="TL;DR", description=description)
        await ctx.send(embed=embed, hidden=True)
        return
    new_messages = []

    if not (startmessageid or endmessageid):
        messages = [message async for message in channel.history(limit=200)]
        messages = messages[::-1]
        # If the last message is from Avrae, remove it
        if messages[-1].author.name == "Avrae":
            messages.pop()

        # Find the most recent message from Avrae, and remove all messages before it
        for i in range(len(messages)):
            if messages[i].author.name == "Avrae":
                new_messages = messages[i:]
        if len(new_messages) != 0:
            messages = new_messages

    elif not (startmessageid and endmessageid):
        description = "If no message IDs are provided, the bot will export the most recent scene in this channel. If _both_ are provided, the bot will export the scene in between them.\n\nNot sure what to do with only one message ID."
        embed = Embed(title="TL;DR", description=description)
        await ctx.send(embed=embed, hidden=True)
        return


    else:
        try:
            startmessageid = int(startmessageid)
            endmessageid = int(endmessageid)
        except:
            description = "Message IDs should be numbers. Please ensure you have copied them correctly."
            embed = Embed(title="TL;DR", description=description)
            await ctx.send(embed=embed, hidden=True)
            return
        messages = [message async for message in channel.history(limit=1000)]
        messages = messages[::-1]
        if startmessageid not in [message.id for message in messages] or endmessageid not in [message.id for message in messages]:
            description = "The start and end messages IDs for this scene could not be found. Please ensure they are in this channel and copied correctly. Note this requires message IDs, not message links."
            embed = Embed(title="TL;DR", description=description)
            await ctx.send(embed=embed, hidden=True)
            return

        for i, message in enumerate(messages):
            if message.id == startmessageid:
                new_messages = messages[i:]
                break
        for i, message in enumerate(new_messages):
            if message.id == endmessageid:
                new_messages = new_messages[:i+1]
                break
    # Create a text file with the scene
    filename = f"{ctx.channel.name}_scene.txt"
    with open(filename, "w") as file:
        for message in new_messages:
            file.write(f"{message.author.name}\n-----\n {message.content}\n===============\n")
    await ctx.send(title="Scene Export", description="Find your scene attached!", file=discord.File(filename), hidden=True)
    return

bot.run(os.getenv("discord"))
