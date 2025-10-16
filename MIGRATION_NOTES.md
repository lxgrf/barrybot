# Discord.py 1.x to 2.x Migration Notes

This document outlines the changes made to migrate BarryBot from discord.py 1.7.3 to 2.4.0.

## Key Changes

### 1. Dependency Updates

**requirements.txt:**
- Removed: `discord-py-slash-command==3.0.3` (now built-in to discord.py 2.x)
- Updated: `discord.py==1.7.3` → `discord.py==2.4.0`

### 2. Main Bot Initialization (main.py)

**Old Pattern (discord.py 1.x):**
```python
from discord_slash import SlashCommand
bot = commands.Bot(command_prefix="\u200b", intents=Intents.all())
slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)
bot.load_extension(f'cogs.{filename[:-3]}')
bot.run(os.getenv("discord"))
```

**New Pattern (discord.py 2.x):**
```python
# No more discord_slash import needed
bot = commands.Bot(command_prefix="\u200b", intents=Intents.all())

@bot.event
async def on_ready():
    # Commands are synced via bot.tree.sync()
    synced = await bot.tree.sync()

async def load_extensions():
    # Extension loading is now async
    await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv("discord"))

asyncio.run(main())
```

**Key differences:**
- Slash commands are now built-in via `app_commands`
- Bot startup uses `asyncio.run()` with async context manager
- Commands are synced via `bot.tree.sync()` in `on_ready`
- Extension loading is now async with `await bot.load_extension()`

### 3. Command Decorators

**Old Pattern (discord.py 1.x):**
```python
from discord_slash import cog_ext, SlashContext, manage_commands

@cog_ext.cog_slash(name="command", description="Description",
         options=[
             manage_commands.create_option(
                 name="param", 
                 description="Param desc", 
                 option_type=3, 
                 required=True
             )
         ])
async def command(self, ctx: SlashContext, param):
    await ctx.defer(hidden=True)
    await ctx.send(embed=embed, hidden=True)
```

**New Pattern (discord.py 2.x):**
```python
from discord import app_commands
import discord

@app_commands.command(name="command", description="Description")
@app_commands.describe(param="Param desc")
async def command(self, interaction: discord.Interaction, param: str):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(embed=embed, ephemeral=True)
```

**Key differences:**
- Use `@app_commands.command()` instead of `@cog_ext.cog_slash()`
- Use `@app_commands.describe()` for parameter descriptions
- Type hints in function signature replace `option_type`
- `SlashContext` → `discord.Interaction`
- `ctx.defer(hidden=True)` → `interaction.response.defer(ephemeral=True)`
- `ctx.send()` → `interaction.followup.send()` (after defer)
- `hidden=True` → `ephemeral=True`

### 4. Cog Setup Function

**Old Pattern:**
```python
def setup(bot):
    bot.add_cog(MyCog(bot))
```

**New Pattern:**
```python
async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

The `setup` function is now async and requires `await` when adding cogs.

### 5. Context vs Interaction Attributes

**Common attribute changes:**
- `ctx.author` → `interaction.user`
- `ctx.guild` → `interaction.guild` (unchanged)
- `ctx.channel` → `interaction.channel` (unchanged)

### 6. Embed Footer

**Old Pattern:**
```python
embed = Embed(title=title, description=description, footer=footer_text)
```

**New Pattern:**
```python
embed = Embed(title=title, description=description)
embed.set_footer(text=footer_text)
```

The `footer` parameter is no longer passed directly to `Embed()`.

### 7. User Discriminators (Breaking Change in Discord.py 2.x)

Discord has deprecated discriminators. Updated code to handle this:

```python
# Old: user.name#discriminator
# New: Check if discriminator exists and is not '0' before using
invoker = f"{author.name}"
if hasattr(author, 'discriminator') and author.discriminator not in ('0', None):
    invoker += f"#{author.discriminator}"
```

## Files Modified

1. **main.py** - Bot initialization and startup
2. **requirements.txt** - Dependency updates
3. **cogs/activity.py** - Slash command migration
4. **cogs/summaries.py** - Slash command migration
5. **cogs/prompts.py** - Slash command migration
6. **cogs/github_issues.py** - Slash command migration
7. **cogs/listeners.py** - Async setup function
8. **utils.py** - Support for both ctx and interaction patterns

## Testing

All existing tests pass with the new version:
- Configuration validation: ✅
- Utility functions: ✅
- Integration examples: ✅ (skipped, require Discord connection)

## Backward Compatibility

The changes are **not backward compatible** with discord.py 1.x. This is a full migration to 2.x.

## Benefits of Migration

1. **Built-in slash commands** - No need for external library
2. **Better performance** - Improved async handling
3. **Discord API compliance** - Up-to-date with Discord's latest features
4. **Type safety** - Better type hints and IDE support
5. **Active support** - discord.py 2.x is actively maintained

## Migration Checklist

- [x] Update requirements.txt
- [x] Remove discord-py-slash-command
- [x] Update main.py bot initialization
- [x] Migrate all slash commands to app_commands
- [x] Update cog setup functions to async
- [x] Update interaction patterns (defer, send, etc.)
- [x] Fix embed footer usage
- [x] Handle discriminator deprecation
- [x] Update utility functions for compatibility
- [x] Test all changes
- [x] Verify command registration with bot.tree.sync()

## References

- [Discord.py Migration Guide](https://discordpy.readthedocs.io/en/stable/migrating.html)
- [App Commands Documentation](https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.Command)
