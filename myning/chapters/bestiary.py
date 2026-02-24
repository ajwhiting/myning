from functools import partial
from typing import Callable

from rich.table import Table

from myning.chapters import Option, PickArgs
from myning.config import MINES
from myning.objects.mine import BossConfig, Mine
from myning.objects.stats import Stats
from myning.utilities.ui import Colors, Icons

stats = Stats()


def enter(back_handler: Callable = None):
    bosses_with_mines: list[tuple[BossConfig, Mine]] = [
        (mine.boss, mine) for mine in MINES.values() if mine.boss is not None
    ]
    total = len(bosses_with_mines)
    defeated_count = sum(1 for boss, _ in bosses_with_mines if boss.name in stats.defeated_bosses)

    options = []
    for boss, mine in bosses_with_mines:
        defeated = boss.name in stats.defeated_bosses
        if defeated:
            label = [Icons.BOSS, boss.name, f"({mine.name})"]
        else:
            label = [Icons.LOCKED, Colors.LOCKED("???"), Colors.LOCKED(f"({mine.name})")]
        options.append(Option(label, partial(show, boss, mine.name, back_handler or enter)))

    if back_handler:
        options.append(Option(["", "Go Back"], back_handler))
    else:
        options.append(Option(["", "Go Back"], enter))

    return PickArgs(
        message=f"Boss Bestiary ({defeated_count}/{total})\n",
        options=options,
    )


def show(boss: BossConfig, mine_name: str, back_handler: Callable):
    defeated = boss.name in stats.defeated_bosses

    if not defeated:
        return PickArgs(
            message=f"{Icons.LOCKED} Unknown Boss\n\n"
            f"Something terrible lurks in [bold]{mine_name}[/]...\n\n"
            "Defeat this boss to unlock its entry.",
            options=[Option("Go Back", partial(enter, back_handler))],
        )

    from myning.utilities.boss_art import render_boss_art  # noqa: PLC0415

    art = render_boss_art(boss)

    stats_table = Table.grid(padding=(0, 1))
    stats_table.add_row("Mine:", mine_name)
    stats_table.add_row("Level:", str(boss.level))
    stats_table.add_row("Reward Multiplier:", f"x{boss.reward_multiplier}")

    content = Table.grid()
    content.add_row(f"[bold]{Icons.BOSS} {boss.name}[/]\n")
    content.add_row(art)

    return PickArgs(
        message=content,
        options=[Option("Go Back", partial(enter, back_handler))],
        subtitle=f"{boss.description}\n" if boss.description else stats_table,
    )
