from myning.config import MINES
from myning.utilities.boss_scaling import get_boss_gold_bonus, get_effective_boss_config


def test_first_boss_keeps_current_difficulty_curve():
    mine = MINES["Hole in the ground"]
    assert mine.boss is not None

    effective_boss = get_effective_boss_config(mine, standard_boost=3.5)

    assert effective_boss.level == mine.boss.level
    assert effective_boss.health_multiplier == mine.boss.health_multiplier
    assert effective_boss.max_item_level == mine.boss.max_item_level
    assert effective_boss.item_scale == mine.boss.item_scale


def test_later_bosses_scale_up_even_without_time_travel_bonus():
    mine = MINES["Cave System"]
    assert mine.boss is not None

    effective_boss = get_effective_boss_config(mine, standard_boost=1)

    assert effective_boss.level > mine.boss.level
    assert effective_boss.health_multiplier > mine.boss.health_multiplier
    assert effective_boss.max_item_level > mine.boss.max_item_level
    assert effective_boss.item_scale > mine.boss.item_scale


def test_time_travel_bonus_pushes_later_bosses_harder():
    mine = MINES["Canyon"]
    assert mine.boss is not None

    base_boss = get_effective_boss_config(mine, standard_boost=1)
    boosted_boss = get_effective_boss_config(mine, standard_boost=2.5)

    assert boosted_boss.level > base_boss.level
    assert boosted_boss.health_multiplier > base_boss.health_multiplier
    assert boosted_boss.max_item_level > base_boss.max_item_level
    assert boosted_boss.item_scale > base_boss.item_scale


def test_boss_gold_bonus_is_awarded_for_level_appropriate_bosses():
    mine = MINES["Cave System"]
    assert mine.boss is not None

    bonus = get_boss_gold_bonus(mine, get_effective_boss_config(mine, standard_boost=1), player_level=18)

    assert bonus > 0


def test_boss_gold_bonus_is_not_awarded_when_overleveled():
    mine = MINES["Small pit"]
    assert mine.boss is not None

    bonus = get_boss_gold_bonus(mine, get_effective_boss_config(mine, standard_boost=1), player_level=10)

    assert bonus == 0
