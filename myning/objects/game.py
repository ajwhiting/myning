from enum import Enum

from myning.objects.object import Object
from myning.objects.singleton import Singleton
from myning.utilities.file_manager import FileManager


class GameState(int, Enum):
    TUTORIAL = 1
    READY = 2


class Game(Object, metaclass=Singleton):
    _state = GameState.TUTORIAL

    @classmethod
    def initialize(cls):
        game = FileManager.load(Game, "game") or cls._create()
        cls._instance = game

    file_name = "game"

    @property
    def state(self) -> GameState:
        return self._state

    @state.setter
    def state(self, value: GameState):
        self._state = value

    def to_dict(self):
        return {
            "state": self._state,
        }

    @classmethod
    def from_dict(cls, dict: dict):
        game = cls._create()
        game._state = dict["state"]
        return game
