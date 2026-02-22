from pathlib import Path

import yaml

from myning.objects.mine import Mine
from myning.objects.species import Species
from myning.objects.upgrade import Upgrade, UpgradeType

_CONFIG_DIR = Path(__file__).parent

CONFIG: dict[str, int] = {}
MINES: dict[str, Mine] = {}
NAMES: dict = {}
RESEARCH: dict[str, Upgrade] = {}
SPECIES: dict[str, Species] = {}
STRINGS: dict = {}
UPGRADES: dict[str, Upgrade] = {}

MARKDOWN_RATIO: int = 0
XP_COST: int = 0
HEAL_TICK_LENGTH: int = 0
MINE_TICK_LENGTH: int = 0
TICK_LENGTH: int = 0
VICTORY_TICK_LENGTH: int = 0


def _load_yaml(filename: str) -> dict:
    with open(_CONFIG_DIR / filename) as f:
        return yaml.safe_load(f)


def load_config():
    """Load all YAML game data. Must be called once at startup before use."""
    global CONFIG, NAMES, STRINGS
    global MARKDOWN_RATIO, XP_COST
    global HEAL_TICK_LENGTH, MINE_TICK_LENGTH, TICK_LENGTH, VICTORY_TICK_LENGTH

    CONFIG = _load_yaml("config.yaml")
    NAMES = _load_yaml("names.yaml")
    STRINGS = _load_yaml("strings.yaml")

    data = _load_yaml("mines.yaml")
    for name, mine in data.items():
        mine["name"] = name
        MINES[name] = Mine.from_dict(mine)

    data = _load_yaml("research.yaml")
    for id, research in data.items():
        research["id"] = id
        RESEARCH[id] = Upgrade.from_dict(research, UpgradeType.RESEARCH)

    data = _load_yaml("species.yaml")
    for id, species in data.items():
        SPECIES[id] = Species.from_dict(species)

    data = _load_yaml("upgrades.yaml")
    for id, upgrade in data.items():
        upgrade["id"] = id
        UPGRADES[id] = Upgrade.from_dict(upgrade)

    MARKDOWN_RATIO = CONFIG["markdown_ratio"]
    XP_COST = CONFIG["xp_cost"]
    HEAL_TICK_LENGTH = CONFIG["heal_tick_length"]
    MINE_TICK_LENGTH = CONFIG["mine_tick_length"]
    TICK_LENGTH = CONFIG["tick_length"]
    VICTORY_TICK_LENGTH = CONFIG["victory_tick_length"]
