"""Command-line entry point.

Examples
--------
Run with the global hotkey (press ``r`` to start/stop)::

    python -m kamil_gamer --game "Tower Defense Sim"

Run a fixed number of cycles headlessly (great for a safe first test)::

    python -m kamil_gamer --game demo --cycles 5
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import Config
from .hotkey import HotkeyRunner


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kamil_gamer", description="Kamil AI Gamer Core")
    p.add_argument("--config", type=Path, default=None, help="path to config.yaml")
    p.add_argument("--game", type=str, default=None, help="game name (for memory)")
    p.add_argument("--hotkey", type=str, default=None, help="toggle key (default r)")
    p.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="run N cycles immediately instead of waiting for the hotkey",
    )
    p.add_argument(
        "--live",
        action="store_true",
        help="actually send mouse/keyboard input (default is dry-run)",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = Config.load(args.config)
    if args.game:
        config.game_name = args.game
    if args.hotkey:
        config.hotkey = args.hotkey
    if args.live:
        config.control.dry_run = False

    mode = "LIVE" if not config.control.dry_run else "DRY-RUN"
    logging.getLogger("kamil_gamer").info(
        "Kamil AI Gamer | game=%s | vision=%s | control=%s",
        config.game_name,
        "LLM+OCR" if config.llm_enabled else "OCR-only",
        mode,
    )

    runner = HotkeyRunner(config)
    if args.cycles is not None:
        stats = runner.orchestrator.run(max_cycles=args.cycles)
        runner.orchestrator.close()
        logging.getLogger("kamil_gamer").info(
            "Done: %d cycles, %d recoveries", stats.cycles, stats.recoveries
        )
        return 0

    runner.listen()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
