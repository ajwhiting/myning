from myning.chapters import Option, PickArgs, bestiary, journal, main_menu
from myning.utilities.ui import Icons


def enter():
    return PickArgs(
        message="Compendium\n",
        options=[
            Option([Icons.JOURNAL, "Species Journal"], lambda: journal.enter(enter)),
            Option([Icons.BOSS, "Boss Bestiary"], lambda: bestiary.enter(enter)),
            Option(["", "Go Back"], main_menu.enter),
        ],
    )
