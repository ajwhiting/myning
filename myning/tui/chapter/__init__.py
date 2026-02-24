import string
from typing import Protocol, runtime_checkable

from rich.text import Text
from textual import events
from textual.containers import ScrollableContainer
from textual.widgets import DataTable

from myning.chapters import (
    AsyncArgs,
    DynamicArgs,
    ExitArgs,
    Handler,
    Option,
    PickArgs,
    main_menu,
    mine,
    tutorial,
)
from myning.chapters.mine.screen import MineScreen
from myning.objects.player import Player
from myning.objects.trip import Trip
from myning.tui.army import ArmyWidget
from myning.tui.chapter.option_table import OptionTable
from myning.tui.chapter.question import Question
from myning.tui.currency import CurrencyWidget
from myning.tui.inventory import InventoryWidget
from myning.utilities.tab_title import TabTitle
from myning.utilities.ui import Icons

player = Player()
trip = Trip()


@runtime_checkable
class ChapterKeyHandler(Protocol):
    """Protocol for widgets that need to handle chapter-level key events.

    Widgets implementing this protocol will receive unhandled keys from ChapterWidget
    and can reserve additional hotkeys (e.g. h/l for left/right navigation).
    """

    extra_hotkey_aliases: dict[str, str]
    """Additional key aliases to register when this widget is active (e.g. {"h": "left"})."""

    async def handle_chapter_key(self, key: str) -> None: ...


_BASE_HOTKEY_ALIASES: dict[str, str] = {
    "j": "down",
    "k": "up",
    "ctrl_d": "pagedown",
    "ctrl_u": "pageup",
}
_BASE_RESERVED_HOTKEYS: frozenset[str] = frozenset({"j", "k", "q"})


def _find_key_handler(widget: "ChapterWidget") -> ChapterKeyHandler | None:
    """Find the first child widget implementing ChapterKeyHandler."""
    for child in widget.children:
        if isinstance(child, ChapterKeyHandler):
            return child
    return None


class ChapterWidget(ScrollableContainer):
    can_focus = True

    def __init__(self):
        self.question = Question()
        self.option_table = OptionTable()
        self.handlers: list[Handler] = []
        self.hotkeys: dict[str, int] = {}
        self.hotkey_aliases: dict[str, str] = dict(_BASE_HOTKEY_ALIASES)
        self.reserved_hotkeys: set[str] = set(_BASE_RESERVED_HOTKEYS)
        super().__init__()

    def compose(self):
        yield self.question
        yield self.option_table

    async def on_mount(self):
        if trip.mine and trip.seconds_left != 0:
            self.update_dashboard()
            self.app.push_screen(
                MineScreen(),
                lambda abandoned: self.pick(mine.complete_trip(abandoned)),
            )
        else:
            self.pick(main_menu.enter() if tutorial.is_complete() else tutorial.enter())

    def on_click(self):
        self.focus()

    async def on_key(self, event: events.Key):
        event.stop()
        key = self.hotkey_aliases.get(event.name, event.name)
        if key == "tab":
            self.app.action_focus_next()
        elif key == "shift_tab":
            self.app.action_focus_previous()
        elif key in ("escape", "q"):
            if not self.option_table.rows or self.option_table.get_row_at(
                self.option_table.row_count - 1
            ) == [Icons.EXIT, "Exit"]:
                return  # Prevent exiting with escape or q in main menu
            await self.select(-1)
        elif key in self.hotkeys:
            await self.select(self.hotkeys[key])
        elif key.isdigit() and key != "0":
            self.option_table.move_cursor(row=int(key) - 1)
        elif key in ("upper_h", "ctrl_b"):
            self.option_table.scroll_page_left()
        elif key in ("upper_l", "ctrl_f"):
            self.option_table.scroll_page_right()
        elif handler := _find_key_handler(self):
            await handler.handle_chapter_key(key)
        elif bindings := self.option_table._bindings.key_to_bindings.get(  # pylint: disable=protected-access
            key
        ):
            await self.option_table.run_action(bindings[0].action)

    async def on_data_table_row_selected(self, row: DataTable.RowSelected):
        self.focus()
        await self.select(row.cursor_row)

    def update_dashboard(self):
        self.screen.query_one(ArmyWidget).update()
        self.screen.query_one(CurrencyWidget).refresh()
        self.screen.query_one(InventoryWidget).update()

    def _sync_hotkey_overrides(self):
        """Add/remove hotkey aliases based on whether a ChapterKeyHandler is mounted."""
        handler = _find_key_handler(self)
        self.hotkey_aliases = dict(_BASE_HOTKEY_ALIASES)
        self.reserved_hotkeys = set(_BASE_RESERVED_HOTKEYS)
        if handler:
            self.hotkey_aliases.update(handler.extra_hotkey_aliases)
            self.reserved_hotkeys.update(handler.extra_hotkey_aliases)

    def pick(self, args: PickArgs):
        self.update_dashboard()
        if title := args.border_title:
            self.border_title = title
            TabTitle.change_tab_status(title)
        self.question.message = args.message
        self.question.subtitle = args.subtitle or ""
        self._sync_hotkey_overrides()
        options, hotkeys = get_labels_and_hotkeys(args.options, self.reserved_hotkeys)
        self.option_table.clear(columns=True)
        if options:
            column_count = max(len(option) for option in options)
            if args.column_titles:
                self.option_table.show_header = True
                while len(args.column_titles) < column_count:
                    args.column_titles.append("")
                self.option_table.add_columns(*args.column_titles)
            else:
                self.option_table.show_header = False
                self.option_table.add_columns(*(str(i) for i in range(column_count)))
            self.option_table.add_rows(options)
        self.hotkeys = hotkeys
        self.handlers = [opt.handler for opt in args.options]

    async def select(self, option_index: int):
        if not self.handlers or option_index >= len(self.handlers):
            return
        handler = self.handlers[option_index]
        args = handler()
        if isinstance(args, ExitArgs):
            self.app.exit()
        elif isinstance(args, DynamicArgs):
            args.callback(self)
        elif isinstance(args, AsyncArgs):
            await args.callback(self)
        else:
            if not args.border_title:
                if (module := handler.__module__.rpartition(".")[-1]) not in (
                    "functools",
                    "pick",
                ) and "base" not in module:
                    args.border_title = module.replace("_", " ").title()
            self.pick(args)

    def clear(self):
        self.pick(PickArgs(message="", options=[]))


def get_labels_and_hotkeys(
    options: list[Option], reserved_hotkeys: set[str]
) -> tuple[list[list[str | Text]], dict[str, int]]:
    hotkeys: dict[str, int] = {}
    labels: list[list[str | Text]] = []
    # The last Option is always assumed to be back or continue, so it defaults to no hotkey
    if options:
        options[-1].enable_hotkeys = False
    for option_index, option in enumerate(options):
        if not isinstance(option.label, list):
            option.label = [option.label]

        if not option.enable_hotkeys:
            labels.append(option.label)
            continue

        text_option_index = None
        text_option = None
        for index, item in enumerate(option.label):
            if isinstance(item, str) and any(c in string.ascii_letters for c in item):
                text_option = Text.from_markup(item)
                text_option_index = index
                break
            if isinstance(item, Text):
                text_option = item
                text_option_index = index
                break

        if text_option and text_option_index is not None:
            hotkey, hotkey_index = get_hotkey(text_option.plain, hotkeys, reserved_hotkeys)
            if hotkey and hotkey_index is not None:
                hotkeys[hotkey] = option_index
                text_option.stylize("underline", hotkey_index, hotkey_index + 1)
                option.label[text_option_index] = text_option

        labels.append(option.label)
    return labels, hotkeys


def get_hotkey(
    label: str, hotkeys: dict[str, int], reserved_hotkeys: set[str]
) -> tuple[None, None] | tuple[str, int]:
    for hotkey_index, char in enumerate(label):
        hotkey = char.lower()
        if hotkey in string.ascii_lowercase and hotkey not in reserved_hotkeys | set(hotkeys):
            return hotkey, hotkey_index
    return None, None
