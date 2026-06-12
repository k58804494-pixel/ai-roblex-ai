"""Game adapters: keep the brain game-agnostic.

The agent's brain (vision -> plan -> control -> memory) is general. Each *game*
or *platform* differs in how you launch it, how its HUD looks, and what keys do
what. An adapter encapsulates those game-specific details behind a common
interface so the same brain can play many games:

    Game Layer
        |
        +-- RobloxAdapter      (test in Roblox Studio first, then Roblox)
        +-- (future) MinecraftAdapter / SteamAdapter / BrowserAdapter
"""

from .base import GameAdapter, KeyBindings, get_adapter, register_adapter
from .roblox import RobloxAdapter

__all__ = [
    "GameAdapter",
    "KeyBindings",
    "RobloxAdapter",
    "get_adapter",
    "register_adapter",
]
