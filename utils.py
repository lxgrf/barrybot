from discord import Embed
import anthropic
import os
import config

anthro = anthropic.Anthropic(
    api_key = os.getenv("anthropic")
)

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

def _ai_enabled_server(guild_id):
    """Check if a server has AI capabilities enabled."""
    return str(guild_id) in config.ai_enabled_servers

def claude_call(prompt, max_tokens=200, temperature=0.8):
    message = anthro.messages.create(
        # model="claude-3-opus-20240229",
        # model = "claude-3-sonnet-20240229",
        model = "claude-3-5-sonnet-20240620",
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

async def get_recent_messages_reversed(channel, limit=25, oldest_first=False):
    # First, get the most recent 'limit' messages
    recent_messages = []
    async for message in channel.history(limit=limit):
        recent_messages.append(message)
    # Then reverse this list
    if oldest_first:
        recent_messages[::-1]
    return recent_messages 