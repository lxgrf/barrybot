"""Small helper utilities for the Listeners cog kept out of the main file."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, cast


logger = logging.getLogger(__name__)

TFunc = TypeVar("TFunc", bound=Callable[..., Awaitable[Any]])


def requires_not_ignored(func: TFunc) -> TFunc:
    """Skip a handler if the triggering user cannot be resolved or is ignored."""

    @wraps(func)
    async def wrapper(self, message, *args, **kwargs):  # type: ignore[override]
        try:
            triggering_user = self._resolve_triggering_user(message)
        except Exception:
            # If resolution fails, skip to be safe
            logger.debug("Skipping %s because triggering user resolution raised", func.__name__)
            return None

        if not triggering_user:
            # Unknown originator; don't run the action to avoid unexpected replies
            logger.debug("Skipping %s because triggering user could not be resolved", func.__name__)
            return None

        try:
            if self._is_user_ignored(
                user_id=triggering_user.get("user_id"),
                username=triggering_user.get("username"),
            ):
                logger.info(
                    "Suppressed %s for ignored user %s",
                    func.__name__,
                    triggering_user.get("username") or triggering_user.get("user_id"),
                )
                return None
        except Exception:
            # On any error checking ignore list, proceed with the action
            logger.exception("Error while checking ignore list in requires_not_ignored decorator")

        return await func(self, message, *args, **kwargs)

    return cast(TFunc, wrapper)


async def setup(bot):
    """No-op setup so extension loader can import this helper module safely.

    The project loads all .py files under `cogs/` as extensions; helper modules
    that don't expose cogs can provide a harmless `setup` entry point to
    avoid load-time errors. This is intentionally a no-op.
    """
    return None

