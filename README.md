# Kamil AI Gamer Core 🎮🧠

A general **game-playing AI framework**. It watches the screen like a player,
reasons about what it sees, controls the mouse and keyboard, recovers when it
gets stuck, and **remembers what it learns** so it does better next time.

Press **`R`** to turn the agent on or off.

> **Milestone this targets:** *join a game → read the screen → take actions →
> recover from getting stuck → remember it next time.* That single loop proves
> most of the architecture; everything else builds upward from it.

---

## ⚠️ Please read first (Terms of Service)

Automating gameplay can violate a game's Terms of Service. In particular,
**Roblox prohibits automation/botting**, and using this on a Roblox account can
get that account **banned**.

This project is a **general, educational game-playing framework**. It does
**not** include anti-cheat / detection-evasion features, and it is not intended
to gain an unfair advantage over other players. The natural-input helpers exist
to make the agent behave less robotically — not to hide it from anti-cheat. Use
it on games and accounts where you accept the risk, and prefer single-player,
sandbox, or open-source games for experimentation.

---

## How it works

```
        ┌──────────────┐
        │  Screenshot  │   (mss screen capture)
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │    Vision    │   LLM scene understanding (optional) + OCR fallback
        └──────┬───────┘
               ▼
        ┌──────────────┐    Scene (health, enemies, quests, buttons, chat...)
        │    Planner   │   rule-based policy -> next Action
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │  Controller  │   pynput mouse/keyboard with natural timing & motion
        └──────┬───────┘
               ▼
        ┌──────────────┐
        │     Game     │
        └──────────────┘

   ↕ Memory (per-game SQLite: facts, events, goals)
   ↕ Anti-stuck (no progress for N seconds → recovery mode)
```

Each layer is a small, swappable module so the long-term **multi-agent brain**
(Vision / Planner / Research / Memory / Critic / Controller / Social agents) can
grow on top of this working foundation.

| Layer | Module | What it does |
|-------|--------|--------------|
| Vision | `kamil_gamer/vision/` | capture → structured `Scene` (LLM + OCR) |
| Control | `kamil_gamer/control/` | execute `Action`s with human-like timing/motion |
| Planning | `kamil_gamer/planning/` | `Scene` → `Action`; short/medium/long-term goals |
| Memory | `kamil_gamer/memory/` | per-game facts, event log, goal progress (SQLite) |
| Anti-stuck | `kamil_gamer/agents/antistuck.py` | detect no-progress, cycle recovery strategies |
| Orchestrator | `kamil_gamer/agents/orchestrator.py` | the perceive→plan→act→remember loop |
| Hotkey | `kamil_gamer/hotkey.py` | press `R` to start/stop |
| Adapters | `kamil_gamer/adapters/` | per-game/platform glue (`RobloxAdapter`, generic base) |
| World model | `kamil_gamer/world/` | internal map: places, connections, danger zones, routing |
| Skill library | `kamil_gamer/skills/` | reusable named skills (parkour/combat/explore/trade) |
| Control Room | `kamil_gamer/control_room/` | chat = command + conversation, mission board, thinking/confidence, clarification |
| Safety | `kamil_gamer/safety.py` | refuses cheating/exploits/harassment; protects your account |
| Personality | `kamil_gamer/personality.py` | trait presets that bias playstyle |
| Metrics | `kamil_gamer/metrics.py` | self-improvement scoreboard + auto weakness flags |

See [`docs/TRAINING.md`](docs/TRAINING.md) for how to **train** the agent
(system prompt + a Roblox-Studio-first curriculum).

### Control Room (chat + missions)

```python
from kamil_gamer.control_room import ChatRouter, MissionBoard

board = MissionBoard()
router = ChatRouter(board)
router.handle("collect 5 coins")   # -> a mission with subgoals + status
router.handle("I like stealth")    # -> remembered as a preference
router.handle("/status")           # -> renders the mission board
router.handle("use a wallhack")    # -> refused by the safety policy
```

## Install

```bash
git clone <this-repo>
cd kamil-ai-gamer
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all,dev]"
```

For OCR you also need the Tesseract binary:

```bash
# Ubuntu/Debian
sudo apt-get install -y tesseract-ocr
# macOS
brew install tesseract
```

### Brains: how it "sees" and reasons

The vision pipeline picks the best available backend automatically, in this
order, and always falls through to something:

1. **Cloud LLM** — set `OPENAI_API_KEY` to use a hosted vision model.
   ```bash
   export OPENAI_API_KEY=sk-...
   ```
2. **Local LLM via Ollama — FREE, no API key** (recommended). Install
   [Ollama](https://ollama.com) on the machine that runs the game and pull a
   vision + text model; the agent talks to it at `localhost:11434`:
   ```bash
   ollama pull llava       # vision: scene understanding
   ollama pull llama3.2    # text: reasoning / natural chat
   ```
3. **OCR heuristics** — Tesseract + regex, always available as a last resort.

Independently, **local YOLO object detection** (also free, offline) can add
bounding boxes for the planner to click:

```bash
pip install -e ".[detect]"   # installs ultralytics (pulls in torch)
```

> Pretrained YOLO weights detect generic **COCO** objects (person, car, …). For
> game-specific things (coins, zombies, chests), train a small custom YOLO model
> and point `yolo.weights` at it — see [`docs/TRAINING.md`](docs/TRAINING.md).

All of this is configured in `config.yaml` (`local_llm:` and `yolo:` sections);
copy `config.example.yaml` to start.

## Run

Safe first run — no input is sent, just a few cycles printed (dry-run is the
default):

```bash
python -m kamil_gamer --game demo --cycles 5 -v
```

Interactive — press **`R`** to start/stop the agent on whatever game is
focused:

```bash
python -m kamil_gamer --game "My Game"
```

Let it actually control the mouse/keyboard (only when you're ready):

```bash
python -m kamil_gamer --game "My Game" --live
```

Configuration lives in `config.yaml` (copy from `config.example.yaml`).

## Memory

Each game gets its own SQLite database under `~/.kamil_gamer/<game>.db` storing:

- **facts** — durable knowledge (e.g. `boss_weakness = "fire"`),
- **events** — a log of actions/recoveries for self-reflection,
- **goals** — long-term objectives and their progress.

This is what lets the agent "remember how to do it next time."

## Roadmap

**Built so far:** vision (LLM+OCR), control + humanization, planner, per-game
memory, anti-stuck, `R` hotkey, adapters (Roblox), world model, skill library,
Control Room (chat + missions + thinking/confidence + clarification), safety,
personality, and self-improvement metrics.

**Planned next (the *Kamil AI Gamer X* dream):**

- **Auto-research engine** — detect the game, read its wiki/guides, build a
  strategy manual before playing.
- **Self-reflection** — after each session, analyse the event log + metrics and
  update memory ("lost boss fight → level up first").
- **Multi-agent brain** — split stages into cooperating agents.
- **Curiosity / experimentation engine** — try things to discover mechanics.
- **Voice companion** — listen to and speak in voice chat.
- **Replay analysis** — record sessions and review mistakes.
- **Team coordination** — multiple AI companions with roles (tank/healer/scout).
- **More adapters** — Minecraft / Steam / browser games.
- **Object detection / minimap reading / motion prediction** in the vision layer.

## Tests

```bash
pytest -q
ruff check .
```

## License

MIT
