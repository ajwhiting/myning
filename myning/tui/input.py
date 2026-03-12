from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.validation import Number
from textual.widgets import Input, Static

from myning.utilities.formatter import Formatter


class IntInput(Input):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, restrict=r"\d*", **kwargs)

    def check_consume_key(self, key: str, character: str | None = None) -> bool:
        """Only consume digit keys so non-digit bindings (like 'q') propagate."""
        if character is not None and not character.isdigit():
            return False
        return super().check_consume_key(key, character)


class IntInputScreen(ModalScreen[int | None]):
    AUTO_FOCUS = "IntInput"
    BINDINGS = [
        ("escape", "cancel", "cancel"),
        Binding("q", "cancel", "cancel", priority=True),
    ]

    def __init__(
        self,
        question: str,
        *,
        placeholder: str | None = None,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> None:
        self.question = question
        self.input = IntInput(
            placeholder=placeholder or "",
            validators=[Number(minimum=minimum, maximum=maximum)],
        )
        if minimum is not None and maximum is not None:
            error = f"Please enter a number between {minimum} and {maximum}"
        elif minimum is not None:
            error = f"Please enter a number greater than or equal to {minimum}"
        elif maximum is not None:
            error = f"Please enter a number less than or equal to {maximum}"
        else:
            error = ""
        self.error = Static(error, id="error")
        super().__init__()

    def compose(self):
        with Vertical():
            yield Static(self.question)
            yield self.input
            yield Static(Formatter.locked("Press escape or q to cancel"))

    def on_mount(self) -> None:
        self.set_focus(self.input)

    def on_input_changed(self):
        if self.error.is_attached:
            self.error.remove()

    def on_input_submitted(self, event: Input.Submitted):
        if event.validation_result and event.validation_result.is_valid:
            self.dismiss(int(event.value))
        else:
            self.query_one(Vertical).mount(self.error, before=-1)

    def action_cancel(self):
        self.dismiss(None)
