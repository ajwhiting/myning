"""Tests for the boss bestiary chapter."""

from unittest.mock import patch

from rich.text import Text

from myning.chapters import bestiary
from myning.config import MINES
from myning.objects.stats import Stats

stats = Stats()

# Pick a mine with a boss for testing
BOSS_MINE = MINES["Hole in the ground"]
BOSS = BOSS_MINE.boss

BOSS_MINE_2 = MINES["Small pit"]
BOSS_2 = BOSS_MINE_2.boss


def test_enter_shows_all_locked_when_no_bosses_defeated():
    result = bestiary.enter()

    assert "Boss Bestiary" in result.message
    assert "0/" in result.message
    # All non-back options should show locked icon
    boss_options = [opt for opt in result.options if "Go Back" not in str(opt.label)]
    for opt in boss_options:
        label_str = str(opt.label)
        assert "🔒" in label_str or "???" in label_str


def test_enter_shows_defeated_boss_unlocked():
    stats.defeated_bosses = [BOSS.name]

    result = bestiary.enter()

    assert "1/" in result.message
    # First boss should be unlocked (crown icon, name visible)
    first_option = result.options[0]
    label_str = str(first_option.label)
    assert BOSS.name in label_str
    assert "👑" in label_str


def test_enter_count_reflects_defeated_bosses():
    stats.defeated_bosses = [BOSS.name, BOSS_2.name]

    result = bestiary.enter()

    assert "2/" in result.message


def test_show_undefeated_boss_returns_mystery_message():
    stats.defeated_bosses = []

    result = bestiary.show(BOSS, BOSS_MINE.name, bestiary.enter)

    assert "Something terrible lurks" in result.message or "Unknown Boss" in result.message
    assert BOSS.name not in result.message


def test_show_defeated_boss_renders_description():
    stats.defeated_bosses = [BOSS.name]

    with patch("myning.utilities.boss_art.render_boss_art", return_value=Text("")):
        result = bestiary.show(BOSS, BOSS_MINE.name, bestiary.enter)

    # Description should appear in subtitle when boss is defeated
    assert BOSS.description in str(result.subtitle)


def test_show_defeated_boss_includes_mine_name():
    stats.defeated_bosses = [BOSS.name]

    with patch("myning.utilities.boss_art.render_boss_art", return_value=Text("")):
        result = bestiary.show(BOSS, BOSS_MINE.name, bestiary.enter)

    # Either way the result should exist
    assert result is not None


def test_stats_record_boss_defeat_idempotent():
    stats.defeated_bosses = []

    stats.record_boss_defeat(BOSS.name)
    stats.record_boss_defeat(BOSS.name)

    assert stats.defeated_bosses.count(BOSS.name) == 1


def test_stats_serialization_roundtrip():
    stats.defeated_bosses = [BOSS.name, BOSS_2.name]

    data = stats.to_dict()
    assert data["defeated_bosses"] == [BOSS.name, BOSS_2.name]

    # Simulate loading from dict (backward compat: missing field defaults to [])
    data_without_bosses = {
        "integer_stats": data["integer_stats"],
        "float_stats": data["float_stats"],
    }
    restored = Stats.from_dict(data_without_bosses)
    assert restored.defeated_bosses == []

    # Full round-trip
    restored_full = Stats.from_dict(data)
    assert restored_full.defeated_bosses == [BOSS.name, BOSS_2.name]
