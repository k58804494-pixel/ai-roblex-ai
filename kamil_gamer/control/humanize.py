"""Human-like timing and motion helpers.

These exist to make the agent's input *natural* (variable reaction time, eased
mouse paths, small aiming noise) rather than to evade anti-cheat. They make the
agent behave more like a person and feel less robotic while playing alongside
humans.
"""

from __future__ import annotations

import math
import random


def reaction_delay(min_ms: int, max_ms: int) -> float:
    """A randomised reaction time in seconds, skewed toward the faster end."""

    lo, hi = min_ms / 1000.0, max_ms / 1000.0
    # Beta(2,5) skews toward lo, mimicking a typical human reaction distribution.
    return lo + (hi - lo) * random.betavariate(2, 5)


def aim_jitter(point: tuple[int, int], sigma_px: int) -> tuple[int, int]:
    """Add gaussian aiming error so the agent does not click pixel-perfectly."""

    if sigma_px <= 0:
        return point
    x = int(round(point[0] + random.gauss(0, sigma_px)))
    y = int(round(point[1] + random.gauss(0, sigma_px)))
    return (x, y)


def _ease_in_out(t: float) -> float:
    return 3 * t * t - 2 * t * t * t


def mouse_path(
    start: tuple[int, int],
    end: tuple[int, int],
    steps: int = 24,
    curve_px: float = 18.0,
) -> list[tuple[int, int]]:
    """Generate an eased, slightly-curved path between two points.

    A perpendicular bezier-style control offset gives the motion a natural arc
    instead of a straight robotic line.
    """

    steps = max(2, steps)
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length = math.hypot(dx, dy) or 1.0
    # Perpendicular unit vector for the arc offset.
    px, py = -dy / length, dx / length
    arc = random.uniform(-curve_px, curve_px)

    path: list[tuple[int, int]] = []
    for i in range(steps + 1):
        t = i / steps
        e = _ease_in_out(t)
        # Quadratic-ish bulge that peaks mid-path (4*t*(1-t)).
        bulge = arc * (4 * t * (1 - t))
        x = sx + dx * e + px * bulge
        y = sy + dy * e + py * bulge
        path.append((int(round(x)), int(round(y))))
    return path
