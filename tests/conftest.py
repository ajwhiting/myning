"""Pytest conftest file."""

from unittest.mock import patch

import pytest

from myning.objects.game import Game, GameState
from myning.objects.garden import Garden
from myning.objects.graveyard import Graveyard
from myning.objects.inventory import Inventory
from myning.objects.macguffin import Macguffin
from myning.objects.player import Player
from myning.objects.research_facility import ResearchFacility
from myning.objects.settings import Settings
from myning.objects.stats import Stats
from myning.objects.trip import Trip

# pylint: disable=redefined-outer-name

# Initialize ALL singletons before app/chapter modules are imported, since they
# reference singletons at module level (e.g. ``player = Player()``).
Player.initialize("MockPlayer")
player = Player()
player.reset()

Game.initialize()
game = Game()
game._state = GameState.READY  # pylint: disable=protected-access

Garden.initialize()
Graveyard.initialize()
Inventory.initialize()
Macguffin.initialize()
ResearchFacility.initialize()
Settings.initialize()
settings = Settings()
settings.mini_games_disabled = False

Stats.initialize()
Trip.initialize()

inventory = Inventory()
inventory._items = {}  # pylint: disable=protected-access

trip = Trip()
trip.clear()

# Import tui modules after objects
# pylint: disable=wrong-import-position
from myning.tui.app import MyningApp
from myning.tui.chapter import ChapterWidget


def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        help="Run tests in headed mode",
    )


@pytest.fixture(autouse=True)
def mock_save():
    """Mock file save operations so tests never write to .data/ or the SQLite DB."""
    with (
        patch("myning.utilities.file_manager.FileManager.save"),
        patch("myning.utilities.file_manager.FileManager.multi_save"),
    ):
        yield


@pytest.fixture(autouse=True)
def reset_objects():
    player.reset()
    inventory._items = {}  # pylint: disable=protected-access
    trip.clear()
    settings.mini_games_disabled = False


@pytest.fixture
async def app_and_pilot(request):
    app = MyningApp()
    headed = request.config.getoption("--headed")
    async with app.run_test(headless=not headed) as pilot:
        yield app, pilot


@pytest.fixture
def app(app_and_pilot):
    app, _ = app_and_pilot
    yield app


@pytest.fixture
def pilot(app_and_pilot):
    _, pilot = app_and_pilot
    yield pilot


@pytest.fixture
def chapter(app: MyningApp):
    yield app.screen.query_one("ChapterWidget", ChapterWidget)
