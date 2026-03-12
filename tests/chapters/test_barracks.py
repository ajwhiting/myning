import pytest
from textual.pilot import Pilot
from textual.widgets import Input

from myning.chapters import barracks
from myning.objects.player import Player
from myning.tui.app import MyningApp
from myning.tui.chapter import ChapterWidget
from myning.tui.input import IntInputScreen
from myning.utilities.generators import generate_character

player = Player()


@pytest.fixture
def ally():
    character = generate_character((1, 1), max_items=0)
    player.add_ally(character)
    yield character
    player.fire_ally(character)


async def test_xp_input_accepts_digits(app: MyningApp, pilot: Pilot, chapter: ChapterWidget, ally):
    """Digits typed into the XP input field should appear in the field."""
    player.exp_available = 100
    chapter.pick(barracks.enter())
    await pilot.pause(0.1)

    # Open the XP input for the first option (player or ally)
    await pilot.press("enter")
    await pilot.pause(0.1)

    assert isinstance(app.screen, IntInputScreen)

    await pilot.press("5", "0")
    await pilot.pause(0.1)

    inp = app.screen.query_one(Input)
    assert inp.value == "50"


async def test_xp_input_rejects_non_digits(
    app: MyningApp, pilot: Pilot, chapter: ChapterWidget, ally
):
    """Non-digit characters typed into the XP input should be silently rejected."""
    player.exp_available = 100
    chapter.pick(barracks.enter())
    await pilot.pause(0.1)

    await pilot.press("enter")
    await pilot.pause(0.1)

    assert isinstance(app.screen, IntInputScreen)

    await pilot.press("5", "a", "b", "0")
    await pilot.pause(0.1)

    inp = app.screen.query_one(Input)
    assert inp.value == "50"


async def test_xp_input_has_focus(app: MyningApp, pilot: Pilot, chapter: ChapterWidget, ally):
    """IntInput should have focus after IntInputScreen is pushed."""
    player.exp_available = 100
    chapter.pick(barracks.enter())
    await pilot.pause(0.1)

    await pilot.press("enter")
    await pilot.pause(0.1)

    assert isinstance(app.screen, IntInputScreen)
    inp = app.screen.query_one(Input)
    assert inp.has_focus, f"IntInput should have focus but focused widget is {app.focused}"


async def test_xp_input_q_cancels(app: MyningApp, pilot: Pilot, chapter: ChapterWidget, ally):
    """Pressing q in the XP input should dismiss the modal."""
    player.exp_available = 100
    original_exp = player.exp_available
    chapter.pick(barracks.enter())
    await pilot.pause(0.1)

    await pilot.press("enter")
    await pilot.pause(0.1)

    assert isinstance(app.screen, IntInputScreen)

    await pilot.press("q")
    await pilot.pause(0.1)

    assert not isinstance(app.screen, IntInputScreen), "q should dismiss IntInputScreen"
    assert player.exp_available == original_exp


async def test_xp_input_cancel(app: MyningApp, pilot: Pilot, chapter: ChapterWidget, ally):
    """Pressing escape or q in the XP input should dismiss without assigning XP."""
    player.exp_available = 100
    original_exp = player.exp_available
    chapter.pick(barracks.enter())
    await pilot.pause(0.1)

    await pilot.press("enter")
    await pilot.pause(0.1)

    assert isinstance(app.screen, IntInputScreen)

    await pilot.press("5", "0")
    await pilot.pause(0.1)

    await pilot.press("escape")
    await pilot.pause(0.1)

    assert not isinstance(app.screen, IntInputScreen)
    assert player.exp_available == original_exp
