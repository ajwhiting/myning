"""Regression tests for boss trigger logic and pick_time message variants."""

from unittest.mock import MagicMock, patch

import pytest
from textual.screen import Screen

from myning.chapters.mine import pick_time
from myning.chapters.mine.screen import MineScreen
from myning.config import MINES
from myning.objects.mine_stats import MineStats
from myning.objects.player import Player
from myning.objects.trip import Trip

player = Player()
trip = Trip()

BOSS_MINE = MINES["Hole in the ground"]


def _make_screen() -> MineScreen:
    """Instantiate MineScreen with Textual widget creation mocked out."""
    with (
        patch("myning.chapters.mine.screen.ScrollableContainer", MagicMock),
        patch("myning.chapters.mine.screen.Static", MagicMock),
        patch("myning.chapters.mine.screen.Vertical", MagicMock),
        patch("myning.chapters.mine.screen.ArmyWidget", MagicMock),
        patch("myning.chapters.mine.screen.ProgressBar", MagicMock),
        patch.object(Screen, "__init__", lambda *a, **kw: None),
    ):
        return MineScreen()


def _complete_mine():
    """Set player progress so mine.is_complete() returns True."""
    wc = BOSS_MINE.win_criteria
    player.mine_progressions[BOSS_MINE.name] = MineStats(
        minutes=wc.minutes,
        kills=wc.kills,
        minerals=wc.minerals,
    )


@pytest.fixture(autouse=True)
def setup_boss_mine():
    """Set up a boss mine trip and restore mine state after each test."""
    player.mine_progressions[BOSS_MINE.name] = MineStats(minutes=0, kills=0, minerals=0)
    trip.mine = BOSS_MINE
    trip.start_trip(5 * 60)
    yield
    del player.mine_progressions[BOSS_MINE.name]


def test_first_encounter_triggers_boss_at_threshold():
    """On the first encounter (requirements not met), boss triggers at win-criteria threshold."""
    assert not BOSS_MINE.is_complete(player.get_mine_progress(BOSS_MINE.name))
    assert BOSS_MINE not in player.mines_completed

    screen = _make_screen()

    assert screen.boss_this_trip is True
    assert screen.boss_trigger_elapsed is None  # threshold mode, not time-based


def test_safe_farming_when_complete_but_boss_undefeated():
    """Enter Mine is safe when criteria are met but boss hasn't been defeated yet (Bug 1 regression)."""
    _complete_mine()
    assert BOSS_MINE.is_complete(player.get_mine_progress(BOSS_MINE.name))
    assert BOSS_MINE not in player.mines_completed

    screen = _make_screen()

    assert screen.boss_this_trip is False


@patch("myning.chapters.mine.screen.random.random", return_value=0.9)  # 0.9 > 0.25 → no trigger
def test_repeat_encounter_no_trigger_when_roll_fails(_mock):
    """After boss is defeated, 75% of the time there is no re-encounter."""
    _complete_mine()
    player.mines_completed.append(BOSS_MINE)

    screen = _make_screen()

    assert screen.boss_this_trip is False


def test_pick_time_message_says_safely_when_boss_undefeated():
    """pick_time shows 'safely' when criteria met but boss not yet defeated."""
    _complete_mine()
    assert BOSS_MINE not in player.mines_completed

    result = pick_time(BOSS_MINE)

    assert "safely" in result.message
    assert "random encounter" not in result.message


def test_pick_time_shows_regular_selection_when_boss_defeated():
    """pick_time shows regular time selection when the boss has already been beaten."""
    _complete_mine()
    player.mines_completed.append(BOSS_MINE)

    result = pick_time(BOSS_MINE)

    assert "How long" in result.message
    assert "safely" not in result.message
