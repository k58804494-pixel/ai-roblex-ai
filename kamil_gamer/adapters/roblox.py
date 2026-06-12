"""Roblox adapter.

Default Roblox keybinds (WASD move, Space jump, ``/`` chat). Recovery prefers a
jump because so many Roblox experiences are obbies/parkour where being stuck
usually means a missed jump or a ledge.

Testing workflow
----------------
1. **Roblox Studio first** (recommended, no ToS risk): open your place, press
   *Play* (F5) so a real client view runs, then start the agent with
   ``--game "<place name>"``. Studio lets you build safe test scenarios (a
   coin to collect, a door, a stuck-spot) to validate the loop.
2. **Live Roblox** only once you're satisfied — and remember the ToS/ban risk
   noted in the README.
"""

from __future__ import annotations

from .base import GameAdapter, KeyBindings, register_adapter


class RobloxAdapter(GameAdapter):
    name = "roblox"
    keys = KeyBindings(
        forward="w",
        back="s",
        left="a",
        right="d",
        jump="space",
        interact="e",
        open_map="m",
        open_chat="/",
    )


@register_adapter("roblox")
def _make_roblox() -> GameAdapter:
    return RobloxAdapter()
