# Welcome to Myning

Myning is an idle game designed to be played in your terminal.
Mine for ore, battle enemies, manage your garden, upgrade your gear, and so much more!

![image of myning gameplay](https://github.com/TheRedPanda17/myning/blob/main/images/myning.png?raw=true)

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (dependency and environment manager)

Install `uv` if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Play the Game

Install dependencies:

```bash
make sync
```

Play the game:

```bash
make play
```

## Contributing

### Setup

Install all dependencies (production + dev):

```bash
make sync
```

### Textual User Interface (TUI)

When developing a full-screen terminal application, the Python debugger will not work. Instead, use
the Textual debug console by running `make dev`, which launches both the game and a Textual console
side by side. You can use `print` statements in the code and they will be displayed in the console.

- [Textual documentation](https://textual.textualize.io) (TUI framework)
- [Textual devtools documentation](https://textual.textualize.io/guide/devtools/#console)
- [Rich documentation](https://rich.readthedocs.io/en/stable/) (library for styling and displaying rich text)

### Formatting and Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for both formatting and linting.

Check for issues:

```bash
make lint
```

Auto-fix and format:

```bash
make format
```

### Tests

Run tests:

```bash
make test
```

It may be helpful to visually debug TUI tests by running pytest with the `--headed` option:

```bash
uv run pytest --headed
```

View test coverage:

```bash
open htmlcov/index.html
```
