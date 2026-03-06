from datetime import datetime

from textual.widgets import Static


class HeaderClock(Static):
    def render(self):
        return datetime.now().strftime("%X")

    def on_mount(self) -> None:
        self.set_interval(1, self.refresh)


class Header(Static):
    def compose(self):
        yield Static("💎", id="header-icon")
        yield Static("Myning", id="header-title", classes="text-title")
        yield HeaderClock()
