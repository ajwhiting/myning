from pathlib import Path

import yaml

from myning.objects.mine import Mine
from myning.objects.species import Species
from myning.objects.upgrade import Upgrade, UpgradeType

_CONFIG_DIR = Path(__file__).parent

CONFIG: dict[str, int]
MINES: dict[str, Mine] = {}
RESEARCH: dict[str, Upgrade] = {}
SPECIES: dict[str, Species] = {}
UPGRADES: dict[str, Upgrade] = {}


def _load_yaml(filename: str) -> dict:
    with open(_CONFIG_DIR / filename) as f:
        return yaml.safe_load(f)


CONFIG = _load_yaml("config.yaml")
NAMES = _load_yaml("names.yaml")
STRINGS = _load_yaml("strings.yaml")

for _name, _mine in _load_yaml("mines.yaml").items():
    _mine["name"] = _name
    MINES[_name] = Mine.from_dict(_mine)

for _id, _research in _load_yaml("research.yaml").items():
    _research["id"] = _id
    RESEARCH[_id] = Upgrade.from_dict(_research, UpgradeType.RESEARCH)

for _id, _species in _load_yaml("species.yaml").items():
    SPECIES[_id] = Species.from_dict(_species)

for _id, _upgrade in _load_yaml("upgrades.yaml").items():
    _upgrade["id"] = _id
    UPGRADES[_id] = Upgrade.from_dict(_upgrade)

LOST_RATIO = CONFIG["lost_ratio"]
MARKDOWN_RATIO = CONFIG["markdown_ratio"]
XP_COST = CONFIG["xp_cost"]

HEAL_TICK_LENGTH = CONFIG["heal_tick_length"]
MINE_TICK_LENGTH = CONFIG["mine_tick_length"]
TICK_LENGTH = CONFIG["tick_length"]
VICTORY_TICK_LENGTH = CONFIG["victory_tick_length"]
