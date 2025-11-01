from __future__ import annotations

import asyncio
import logging

from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from bot.core.services import ServiceContainer
from bot.core.settings import build_service_container, load_settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


EXTENSIONS = [
    "bot.extensions.activity",
    "bot.extensions.github_issues",
    "bot.extensions.listeners",
    "bot.extensions.prompts",
    "bot.extensions.summaries",
]


def create_bot(services: ServiceContainer) -> commands.Bot:
    intents = Intents.all()
    bot = commands.Bot(command_prefix="\u200b", intents=intents)
    bot.services = services  # type: ignore[attr-defined]
    return bot


async def on_ready_event(bot: commands.Bot) -> None:
    logger.info("Logged in as %s (ID: %s)", bot.user, getattr(bot.user, "id", "unknown"))
    try:
        synced = await bot.tree.sync()
        logger.info("Synced %d command(s)", len(synced))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to sync commands: %s", exc)

    if not getattr(bot, "_startup_dm_sent", False):
        try:
            target_user = await bot.fetch_user(661212031231459329)
            await target_user.send("Barry is online and ready.")
            logger.info("Sent startup DM to lxgrf (661212031231459329)")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Startup DM failed: %s", exc)
        finally:
            bot._startup_dm_sent = True  # type: ignore[attr-defined]


async def load_extensions(bot: commands.Bot) -> None:
    from discord.ext import commands as commands_module

    for extension in EXTENSIONS:
        try:
            await bot.load_extension(extension)
            logger.info("Loaded extension: %s", extension)
        except commands_module.errors.NoEntryPointError:
            logger.debug("Skipping helper module without setup: %s", extension)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to load extension %s: %s", extension, exc)


async def main() -> None:
    load_dotenv()
    settings = load_settings()
    services = build_service_container()
    bot = create_bot(services)

    @bot.event  # type: ignore[no-redef]
    async def on_ready() -> None:
        await on_ready_event(bot)

    async with bot:
        await load_extensions(bot)
        await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())

