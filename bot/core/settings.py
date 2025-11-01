"""Runtime settings helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass

from bot.core.services import ServiceContainer
from bot.services.github_app import build_github_app_client_from_env


class SettingsError(RuntimeError):
    """Raised when mandatory configuration is missing."""


@dataclass
class Settings:
    """Minimal settings required to run the bot."""

    discord_token: str


def load_settings() -> Settings:
    discord_token = os.getenv("discord")
    if not discord_token:
        raise SettingsError("discord environment variable (Discord bot token) is not set")

    return Settings(discord_token=discord_token)


def build_service_container() -> ServiceContainer:
    """Bootstrap all long-lived services using environment variables."""

    github_client = build_github_app_client_from_env()
    return ServiceContainer(github=github_client)
