# CLAUDE.md

This file provides guidance for AI assistants working in this repository.

## Project Overview

**Myning** is a terminal-based idle/incremental game written in Python. Players mine resources, fight enemies, manage a party of allies, grow a garden, research technologies, and craft equipment — all through a rich Terminal User Interface (TUI) built with Textual. The game persists state as JSON files in a `.data/` directory.

## Development Environment

**Python version:** 3.10 (enforced; use pyenv)

### Setup

```bash
# Create and activate virtualenv with pyenv
make venv        # production dependencies only
make venv-dev    # production + development dependencies

# Install deps into an existing venv
make deps-install

# Recompile pinned dependencies from *.in source files
make deps-compile
```

Dependencies are managed with `pip-tools`. Edit `requirements.in` / `requirements-dev.in` and run `make deps-compile` to update the pinned `requirements.txt` / `requirements-dev.txt`.

## Running the Game

```bash
make play   # production mode (./run.sh)
make dev    # development mode with textual console (./dev.sh)
```

Both scripts restart the game automatically when it exits with:
- Code `123` — time travel (permadeath) mechanic
- Code `122` — game update available

For TUI debugging, `make dev` launches a Textual console alongside the game.

## Code Quality

### Linting (must pass before committing)

```bash
make lint    # runs both isort and black in check mode
```

Individual tools:
```bash
isort . --check --diff   # import ordering
black . --check          # code formatting
```

To auto-fix:
```bash
isort .
black .
```

### Code style rules

- **Line length:** 100 characters (Black + isort both configured to this)
- **Import ordering:** isort with `profile = "black"`
- **Formatter:** Black (no manual style decisions)

## Testing

```bash
make test                  # run full suite with coverage
pytest --headed            # run with visible TUI (useful for debugging chapter tests)
pytest tests/path/to/test  # run a specific test file
```

### Test configuration (`pyproject.toml`)

- Framework: `pytest` with `pytest-asyncio` (`asyncio_mode = "auto"`)
- Coverage: `pytest-cov` — generates terminal + HTML reports
- Test path: `tests/`
- Flags: `-svx` (verbose, stop on first failure)

### Test fixtures (`tests/conftest.py`)

Key fixtures available in all tests:
- `app_and_pilot` — async fixture yielding `(MyningApp, Pilot)` for TUI tests
- `app` — `MyningApp` instance
- `pilot` — Textual `Pilot` for simulating user input
- `chapter` — the `ChapterWidget` from the running app
- `mock_save` *(autouse)* — patches `FileManager.save` and `FileManager.multi_save` so tests never write to disk
- `reset_objects` *(autouse)* — resets player, inventory, and trip state before each test

**Important:** Always initialize singleton objects (Player, Game, Inventory, Trip) before importing TUI modules in tests. See `conftest.py` for the established pattern.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on push/PR to `main`:
1. `isort . --check --diff`
2. `black . --check`
3. `pytest`

All three must pass for a PR to merge.

## Architecture

### Singleton pattern

Most core game state objects use a custom `Singleton` metaclass (`myning/objects/singleton.py`). Singletons must be **initialized once** before use:

```python
Player.initialize("PlayerName")
player = Player()  # returns the same instance everywhere
```

### Object model

All game objects extend `Object` (`myning/objects/object.py`), which provides:
- `to_dict()` — serialize to JSON-compatible dict
- `from_dict(data)` — deserialize from saved data
- A unique `id` field (UUID)

### Chapter system

Game flow is driven by **chapters** (`myning/chapters/`). Each chapter is a function (or set of functions) that returns one of:

| Return type | Meaning |
|-------------|---------|
| `PickArgs` | Show a question with selectable options |
| `DynamicArgs` | Run a callback synchronously |
| `AsyncArgs` | Run an async callback |
| `ExitArgs` | Exit the chapter (go back) |
| `StoryArgs` | Show a narrative message with a single "okay" response |

An `Option` pairs a display label with a `Handler` callable. Chapters are wired together by returning `Option` lists that point to other chapter handlers.

### TUI structure

```
MyningApp (textual App)
└── MyningScreen
    ├── Header
    ├── Body (horizontal layout)
    │   ├── ChapterWidget  ← renders the active chapter
    │   └── SideBar
    │       ├── ArmyWidget
    │       ├── InventoryWidget
    │       └── CurrencyWidget
    └── Footer
```

Hotkeys: vim-style `h/j/k/l` navigation, plus `enter` to select.

### Configuration

Game content (mines, species, upgrades, research) lives in YAML files inside `myning/`. Loaded at startup by `myning/config.py` into module-level dicts:

| File | Dict | Purpose |
|------|------|---------|
| `config.yaml` | `CONFIG` | Balance values (tick rates, XP costs, etc.) |
| `mines.yaml` | `MINES` | Mine definitions with enemies and loot |
| `species.yaml` | `SPECIES` | Playable species with stats and icons |
| `upgrades.yaml` | `UPGRADES` | Equipment upgrade trees |
| `research.yaml` | `RESEARCH` | Tech tree research definitions |
| `names.yaml` | `NAMES` | NPC/item name generation lists |
| `strings.yaml` | `STRINGS` | UI text |

To add new game content, edit the appropriate YAML file — no code changes required for purely data-driven additions.

### Persistence

`FileManager` (`myning/utilities/file_manager.py`) is a singleton that saves/loads JSON to `.data/`. Key files:
- `.data/player.json` — player character
- `.data/stats.json` — global statistics (preserved on time travel reset)
- `.data/settings.json` — game settings (preserved on time travel reset)
- `.data/items/` — inventory items
- `.data/entities/` — ally characters

### API integration

`myning/api/` provides optional leaderboard sync via aiohttp. Requires an API key set in the environment. Not required for local gameplay.

### Migrations

When the save-file format changes, a migration is added to `myning/migrations/`. Run with:

```bash
make migrate id=<migration_name>
# or
python migrate.py <migration_name>
```

## Directory Reference

```
myning/
├── api/              # Leaderboard HTTP client (aiohttp)
├── chapters/         # Game screens/flows
│   ├── mine/         # Core mining gameplay loop
│   └── garden/       # Gardening system
├── migrations/       # Save-file data migrations
├── objects/          # Game state models (singletons + serializable objects)
├── tui/              # Textual TUI components
│   └── chapter/      # ChapterWidget and supporting widgets
├── utilities/        # Shared helpers (formatting, RNG, file I/O, etc.)
├── config.py         # YAML loader; exports MINES, SPECIES, UPGRADES, etc.
├── *.yaml            # Game content data files
tests/
├── conftest.py       # Shared fixtures and singleton initialization
├── chapters/         # Chapter-level integration tests
├── objects/          # Unit tests for game objects
└── utilities/        # Unit tests for utility functions
```

## Key Conventions

1. **Never mutate YAML data files at runtime** — they are read-only configuration.
2. **Use `FileManager.save()` / `FileManager.multi_save()`** for all persistence; do not write files directly.
3. **Singletons initialize once** — call `ClassName.initialize(...)` at startup (see `main.py`), then use `ClassName()` anywhere to get the instance.
4. **Chapter handlers are pure functions** — they receive no arguments and return `PickArgs`, `DynamicArgs`, etc. Side effects happen in callbacks.
5. **Mock saves in tests** — the `mock_save` autouse fixture prevents disk writes. Do not patch it out in individual tests.
6. **Textual version is pinned to 0.32.0** — a specific version is required due to a mine screen border rendering bug. Do not upgrade without testing the mine screen thoroughly.
7. **Exit codes are meaningful** — code `123` triggers time travel restart, code `122` triggers update restart (handled by `run.sh`/`dev.sh`).
