# Training Instructions — teaching Kamil AI Gamer

This is the guide you (the human coach) follow to *train* the agent, plus the
**system instructions** the agent itself runs on. The philosophy is **learn like
a human**: watch, reason, test, learn — not fail a million times.

---

## Part A — The agent's operating instructions (system prompt)

> You are **Kamil AI Gamer**, a general game-playing AI that plays alongside a
> human teammate. You see the screen, reason about it, and control the mouse and
> keyboard like a real player.
>
> **Core loop:** perceive → understand → plan → act → check progress → remember.
>
> **Rules of play:**
> 1. **Be honest about uncertainty.** If your confidence in a goal or objective
>    is below the threshold, *pause and ask the user* — never loop silently.
> 2. **Make progress every cycle.** If nothing changes for a while, you are
>    stuck: switch to recovery (new path, open map, back up, ask) instead of
>    repeating the same action.
> 3. **Remember everything useful.** Locations, NPCs, dangers, what worked, what
>    failed, and the player's preferences go into memory.
> 4. **Play like a human.** Use natural reaction times and movement; don't act
>    with inhuman precision.
> 5. **Stay safe & fair.** Refuse cheating, exploits, harassment, or anything
>    that risks the user's account or breaks game rules.
> 6. **Cooperate.** Follow the player's goals, help beginners, communicate
>    clearly, and explain what you're doing when asked.

Drop this into `LLM`-backed planning/chat layers as the system message.

---

## Part B — How to train it (human coach workflow)

Train in **Roblox Studio first** — it's safe (no ToS risk) and you can build
exactly the scenario you want to teach.

### Curriculum (easy → hard)

1. **See** — Put one clear object on screen (a coin). Confirm the vision layer
   reports it. Fix prompts/labels until perception is reliable.
2. **Move** — Teach it to walk to a target. Validate the controller in
   `dry_run` first, then `--live`.
3. **One simple quest** — "Collect 1 coin." Verify the full loop:
   perceive → plan → act → mission marked ✅ → memory updated.
4. **Get unstuck** — Build a dead-end / locked door. Confirm anti-stuck triggers
   recovery and the agent eventually asks for help.
5. **Remember** — Restart the session. Confirm it recalls the map / what it
   learned (`~/.kamil_gamer/<game>.db`).
6. **Scale up** — "Collect 5 coins", then add enemies, then a boss.

### The teaching signals

- **Demonstrate**: do the task yourself once; the agent logs what it observed.
- **Correct via chat**: "go left", "that's a trap", "talk to the NPC first".
  Corrections become memory (preferences, danger zones, routes).
- **Reflect after each session** (Phase 5): review `recent_events()` and the
  metrics scoreboard; write a memory entry like
  `boss_a: {weakness: "fire", avoid: "ice weapons"}`.

### What "done training a game" looks like (the milestone)

> Joins the game → reads the screen → completes a simple quest → recovers from
> getting stuck → and remembers how to do it next time.

Once that passes, raise the difficulty.

---

## Part C — Where learning is stored

| What | Where |
|------|-------|
| Facts (boss weaknesses, routes) | `GameMemory.remember()` |
| Event log (for reflection) | `GameMemory.log_event()` |
| Goal progress | `GameMemory.set_goal()` |
| Internal map | `WorldModel` (persisted as the `world_model` fact) |
| Player preferences | `player_preferences` fact (set from chat) |
| Reusable skills | `SkillLibrary` |

---

## Part D — Self-improvement

After each session, inspect `Metrics`:

- `success_rate`, `mission_completion_rate`
- `deaths`, `recoveries`, `seconds_stuck`
- `weaknesses()` — auto-flags the worst areas

Use the flagged weaknesses to choose what to drill next session (e.g. "gets
stuck often" → practise the anti-stuck scenario; "low success rate" → improve
vision labels or slow the loop down).
