import math
from dataclasses import replace

from myning.config import MINES
from myning.objects.macguffin import Macguffin
from myning.objects.mine import BossConfig, Mine


def get_boss_mines() -> list[Mine]:
    return [mine for mine in MINES.values() if mine.boss is not None]


def get_boss_tier(mine: Mine) -> int:
    for index, boss_mine in enumerate(get_boss_mines()):
        if boss_mine.name == mine.name:
            return index
    msg = f"Mine '{mine.name}' does not have a boss"
    raise ValueError(msg)


def get_effective_boss_config(mine: Mine, standard_boost: float | None = None) -> BossConfig:
    if mine.boss is None:
        msg = f"Mine '{mine.name}' does not have a boss"
        raise ValueError(msg)

    tier = get_boss_tier(mine)
    prestige_pressure = max(0.0, _get_standard_boost(standard_boost) - 1)

    level_bonus = tier + math.floor(prestige_pressure * max(tier - 0.5, 0))
    health_scale = 1 + (0.05 * tier) + (0.003 * tier * tier) + (0.025 * prestige_pressure * tier)
    item_level_bonus = math.floor(tier / 2) + math.floor(prestige_pressure * tier / 2)
    item_scale_bonus = 1 + (0.02 * tier) + (0.01 * prestige_pressure * tier)

    return replace(
        mine.boss,
        level=mine.boss.level + level_bonus,
        health_multiplier=round(mine.boss.health_multiplier * health_scale, 2),
        max_item_level=mine.boss.max_item_level + item_level_bonus,
        item_scale=round(mine.boss.item_scale * item_scale_bonus, 2),
    )


def get_boss_gold_bonus(mine: Mine, boss_config: BossConfig, player_level: int) -> int:
    tier = get_boss_tier(mine)
    level_window = 3 + (tier // 3)
    if player_level > mine.min_player_level + level_window:
        return 0

    return int(max(25, mine.cost * 0.4, boss_config.level * boss_config.reward_multiplier * 5))


def _get_standard_boost(standard_boost: float | None) -> float:
    if standard_boost is not None:
        return standard_boost
    macguffin = Macguffin()
    return max(macguffin.xp_boost, macguffin.mineral_boost)
