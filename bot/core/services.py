"""Service container wiring for the bot."""

from __future__ import annotations

from dataclasses import dataclass

from bot.services.github_app import GitHubAppClient


@dataclass(slots=True)
class ServiceContainer:
    """Holds long-lived service instances injected into extensions."""

    github: GitHubAppClient
