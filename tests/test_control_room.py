from kamil_gamer.control_room import (
    ChatRouter,
    MissionBoard,
    MissionStatus,
    ThinkingState,
)
from kamil_gamer.control_room.chat import TurnKind
from kamil_gamer.memory import GameMemory


def test_mission_progress_and_completion():
    board = MissionBoard()
    m = board.add("Collect 5 gems", ["Find gems", "Collect them"])
    assert m.status == MissionStatus.NOT_STARTED
    m.complete_next_subgoal()
    assert m.status == MissionStatus.IN_PROGRESS
    m.complete_next_subgoal()
    assert m.status == MissionStatus.COMPLETED
    assert m.progress() == (2, 2)


def test_board_next_actionable_skips_completed():
    board = MissionBoard()
    done = board.add("done")
    done.status = MissionStatus.COMPLETED
    todo = board.add("todo")
    assert board.next_actionable() is todo


def test_chat_imperative_creates_mission():
    board = MissionBoard()
    router = ChatRouter(board)
    turn = router.handle("collect 5 coins")
    assert turn.kind == TurnKind.MISSION
    assert len(board.missions) == 1
    assert board.missions[0].subgoals  # decomposed into subgoals


def test_chat_slash_commands():
    board = MissionBoard()
    router = ChatRouter(board)
    assert router.handle("/goal find the key").kind == TurnKind.MISSION
    assert router.handle("/status").kind == TurnKind.COMMAND
    reset = router.handle("/reset")
    assert reset.kind == TurnKind.COMMAND
    assert board.missions == []


def test_chat_preference_remembered(tmp_path):
    mem = GameMemory(tmp_path, "g")
    router = ChatRouter(MissionBoard(), memory=mem)
    turn = router.handle("I like stealth playstyle")
    assert turn.kind == TurnKind.PREFERENCE
    assert any("stealth" in p for p in mem.recall("player_preferences", []))
    mem.close()


def test_chat_question_is_conversation():
    router = ChatRouter(MissionBoard())
    turn = router.handle("what are you doing?")
    assert turn.kind == TurnKind.CONVERSATION


def test_chat_refuses_unsafe():
    router = ChatRouter(MissionBoard())
    turn = router.handle("install an aimbot to win")
    assert turn.kind == TurnKind.REFUSED


class _FakeLLM:
    available = True

    def chat(self, prompt, system=None):
        return "  Sure, exploring the map now!  "


def test_chat_uses_llm_for_conversation():
    router = ChatRouter(MissionBoard(), llm=_FakeLLM())
    turn = router.handle("what are you doing?")
    assert turn.kind == TurnKind.CONVERSATION
    assert turn.reply == "Sure, exploring the map now!"


def test_chat_falls_back_when_llm_unavailable():
    class _Down:
        available = False

        def chat(self, prompt, system=None):  # pragma: no cover - never called
            raise AssertionError("should not be called when unavailable")

    router = ChatRouter(MissionBoard(), llm=_Down())
    turn = router.handle("what are you doing?")
    assert turn.kind == TurnKind.CONVERSATION
    assert turn.reply  # rule-based fallback still answers


def test_thinking_clarification():
    t = ThinkingState(current_goal="Find key", confidence=0.2, problem="Door locked")
    assert t.needs_clarification()
    assert t.clarifying_question() is not None
    t2 = ThinkingState(confidence=0.9)
    assert not t2.needs_clarification()
    assert t2.clarifying_question() is None
