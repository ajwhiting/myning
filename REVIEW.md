# Codebase Review: Myning

**Goal:** Evaluate Python best practices, abstractions, technology choices, and newcomer readability.

---

## Executive Summary

Myning is a well-structured project with a clear architecture and consistent patterns. The chapter system is elegant and the data-driven YAML approach makes content additions trivial. However, there are several areas where the current design creates unnecessary friction for newcomers:

1. **The Singleton metaclass + initialize pattern** is the single biggest source of confusion
2. **No static type checking** means bugs hide in plain sight (and some already have)
3. **Module-level side effects** in `config.py` and implicit ordering constraints in `main.py` create hidden coupling
4. **The chapter type system** is well-designed but has gaps in its type annotations that make the control flow harder to follow

There are also **real bugs** that static analysis would have caught.

---

## Bugs Found

### 1. `Stats.increment_float_stat` writes to the wrong dict

**File:** `myning/objects/stats.py:91-92`

```python
def increment_float_stat(self, key: FloatStatKeys, increment_by: float):
    self.integer_stats[key.value] = self.integer_stats.get(key.value, 0) + increment_by
```

This writes to `self.integer_stats` instead of `self.float_stats`. A type checker would flag this since `FloatStatKeys` and `IntegerStatKeys` are distinct enums.

### 2. `Player.total_value` counts `upgrades_value` twice

**File:** `myning/objects/player.py:66-74`

```python
return (
    army_value
    + exp_value
    + upgrades_value     # <-- first time
    + unlocked_mines
    + self.gold
    + upgrades_value     # <-- second time (duplicate)
    + beaten_mines
)
```

### 3. `Plant.from_dict` shadows the `cls` parameter

**File:** `myning/objects/plant.py:44-57`

```python
@classmethod
def from_dict(cls, dict: dict):   # 'cls' is the class
    ...
    cls = super().from_dict(dict)  # 'cls' is now an instance
    cls.plant_type = dict["plant_type"]
    ...
    return cls
```

Reassigning `cls` from a class to an instance is confusing. This should use a different variable name (e.g., `plant`). The parameter name `dict` also shadows the built-in.

### 4. Debug `print()` left in production code

**File:** `myning/objects/trip.py:111`

```python
if not item:
    print("Could not find mineral", item_id)
```

This will print to the terminal during normal gameplay if an item is missing from the save file.

### 5. `@classmethod @property` is deprecated

**Files:** `myning/objects/player.py:135-138`, `myning/objects/trip.py:98-101`, `myning/objects/stats.py:43-46`, and others.

```python
@classmethod
@property
def file_name(cls):
    return "player"
```

`@classmethod @property` stacking was never officially supported and was deprecated in Python 3.11. It happens to work in 3.10 but will break on upgrade. These should be plain class attributes or `__init_subclass__` assignments.

---

## Architecture Concerns

### The Singleton + Initialize Pattern

**Files:** `myning/objects/singleton.py`, `main.py:28-39`

This is the #1 source of newcomer confusion. The pattern requires:
1. Call `Player.initialize()` exactly once at startup
2. Then use `Player()` everywhere to get the instance
3. If you forget step 1, `Player()` creates a *new, uninitialized* instance silently
4. If you call `Player("name")` after initialization, it *ignores the argument* and returns the existing instance

Problems:
- **No error on misuse.** Calling `Player()` before `initialize()` silently creates an empty object instead of raising an error. Newcomers will get confusing attribute errors far from the actual mistake.
- **Two paths to set the instance.** `__call__` (normal construction) and `_instance` setter (used by `initialize`) both populate `_instances`. It's unclear which takes precedence.
- **`Singleton.reset()` is a class method on the metaclass.** It clears *all* singletons across the entire application. This is dangerous and non-obvious.
- **Initialization order is implicit.** `main.py:28-39` must initialize singletons in a specific order (FileManager before Player before everything else), but nothing enforces this.

**Recommendation:** Consider replacing with a simple module-level registry or dependency injection container. At minimum, `__call__` should raise `RuntimeError` if `initialize()` hasn't been called yet, so misuse fails loudly.

### Module-Level Side Effects in config.py

**File:** `myning/config.py:14-44`

All YAML files are loaded at import time:
```python
with open("myning/config.yaml", "r") as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)
```

Issues:
- **Import = execution.** Simply importing `config` triggers file I/O. This makes testing harder and debugging confusing.
- **Hardcoded relative paths.** `"myning/config.yaml"` assumes `cwd` is the project root. Running from any other directory breaks the import.
- **No error handling.** A missing or malformed YAML file crashes the entire import chain with an unhelpful traceback.
- **Mutable globals.** `MINES`, `UPGRADES`, etc. are plain dicts that can be mutated at runtime despite the convention against it. `types.MappingProxyType` would enforce immutability.

**Recommendation:** Wrap loading in a function (e.g., `load_config()`) called explicitly from `main.py`, or use `importlib.resources` for path resolution. Use `yaml.safe_load()` instead of `yaml.load(f, Loader=yaml.FullLoader)`.

### Chapter Type System Gaps

**File:** `myning/chapters/__init__.py:36`

```python
Handler = Callable[..., PickArgs | DynamicArgs | AsyncArgs | ExitArgs]
```

- `StoryArgs` is not in the `Handler` union type, but handlers return it throughout the codebase (it gets converted via `story_builder`). This makes the type system incomplete.
- `Callable[...]` accepts any arguments, but handlers are always called with zero arguments (`handler()` at `tui/chapter/__init__.py:150`). Should be `Callable[[], ...]`.
- `functools.partial` is used extensively to bind arguments, which is correct but makes the actual call signature invisible to type checkers and newcomers.

### Implicit Last-Option Mutation

**File:** `myning/tui/chapter/__init__.py:175-176`

```python
if options:
    options[-1].enable_hotkeys = False
```

This mutates the caller's `Option` object. Every chapter must know that its last option will have hotkeys disabled. This is:
- Undocumented in the `Option` dataclass (the docstring exists but is easy to miss)
- A side effect hidden in a helper function
- Surprising when you're building option lists

**Recommendation:** Either make this explicit in the chapter (let chapters mark their own back buttons) or create a `BackOption` subclass.

### Magic Module Name Detection

**File:** `myning/tui/chapter/__init__.py:158-164`

```python
if (module := handler.__module__.rpartition(".")[-1]) not in (
    "functools",
    "pick",
) and "base" not in module:
    title = module.replace("_", " ").title()
```

The border title is inferred from the handler's module name, with a hard-coded exclusion list. This is fragile -- adding a new chapter with "base" in the name would silently skip title updates.

**Recommendation:** Require `border_title` on `PickArgs` (it's already optional). Chapters should declare their own titles rather than having them inferred.

### Garden-Specific Logic in ChapterWidget

**File:** `myning/tui/chapter/__init__.py:118-129`

```python
if self.query("GardenTable"):
    HOTKEY_ALIASES["h"] = "left"
    HOTKEY_ALIASES["l"] = "right"
    RESERVED_HOTKEYS.add("h")
    RESERVED_HOTKEYS.add("l")
```

The generic `ChapterWidget` has hard-coded awareness of `GardenTable`. This breaks the separation between the framework and specific chapters.

**Recommendation:** Let chapters declare their own keybinding overrides (e.g., via a field on `PickArgs` or `DynamicArgs`).

---

## Missing Tooling

### No Static Type Checker

This is the most impactful gap. The codebase has type annotations in many places but nothing validates them. Adding `mypy` or `pyright` to CI would:
- Catch bugs like the `Stats.increment_float_stat` issue above
- Enforce the chapter type contracts
- Help newcomers understand function signatures
- Prevent regressions

**Recommendation:** Add `mypy` (or `pyright`) to `requirements-dev.in` and the CI pipeline. Start with `--ignore-missing-imports` and gradually tighten.

### No Pre-Commit Hooks

Formatting issues only surface in CI, not locally. Contributors push, wait for CI, fix formatting, push again.

**Recommendation:** Add a `pre-commit` configuration with `black`, `isort`, and eventually `mypy`. This catches issues before they leave the developer's machine.

### No Linter Beyond Formatting

`black` and `isort` only handle formatting and import ordering. There's no linter checking for:
- Unused imports/variables
- Shadowed built-ins (like `dict` in `Plant.from_dict`)
- Unreachable code
- Common anti-patterns

**Recommendation:** Add `ruff` (fast, replaces `flake8` + `pylint` + many plugins). It can also replace `isort` and partially replace `black`.

---

## Technology Assessment

| Tool | Verdict | Notes |
|------|---------|-------|
| **Textual** | Good choice | Right tool for terminal TUI. The 0.32.0 pin is a concern for long-term maintenance but understandable. |
| **pip-tools** | Good choice | Simple, reliable dependency management. Appropriate for this project size. |
| **PyYAML** | Fine | Works for the use case. Could consider `ruamel.yaml` for round-trip safety if config editing is ever needed. |
| **pytest + pytest-asyncio** | Good choice | Standard, well-supported. The `asyncio_mode = "auto"` setting is correct. |
| **Black + isort** | Good but replaceable | `ruff format` + `ruff check` can replace both with faster execution and more checks. |
| **Rich** | Good choice | Powers the table rendering. Used appropriately for display formatting. |
| **aiohttp** | Fine | Used only for the optional leaderboard API. Appropriate for async HTTP. |
| **No build system** | Fine for now | The project is a game, not a library. A `[build-system]` in pyproject.toml isn't needed yet. |

---

## Readability for Newcomers: Specific Friction Points

### 1. "Where does state come from?"

Every chapter file starts with:
```python
player = Player()
inventory = Inventory()
```

A newcomer sees `Player()` and thinks "this creates a new Player." Understanding that it returns an existing singleton requires knowing about the metaclass, which requires knowing about `main.py`'s initialization order. This is 3 layers of indirection before you can read chapter code.

### 2. "How does navigation work?"

The chapter system is actually elegant once you understand it, but the entry point is hard to find. A newcomer would need to:
1. Find `main.py` -> `MyningApp().run()`
2. Find `tui/app.py` -> `MyningScreen`
3. Find `tui/chapter/__init__.py` -> `on_mount` -> `main_menu.enter()`
4. Understand that `pick()` renders a `PickArgs`
5. Understand that `select()` calls a handler and dispatches on return type

This is a 5-file journey before you can understand a single screen. A `CONTRIBUTING.md` or architectural diagram would help.

### 3. "What's the difference between DynamicArgs and AsyncArgs?"

The distinction is subtle: `DynamicArgs` runs synchronously, `AsyncArgs` runs as a coroutine. But both take `Callable[["ChapterWidget"], ...]`. A newcomer has to read the dispatch logic in `ChapterWidget.select()` to understand the difference.

### 4. "Why does my chapter's last option behave differently?"

The implicit `enable_hotkeys = False` mutation on the last option is invisible unless you read the `get_labels_and_hotkeys` function. New contributors will wonder why their last option doesn't get a hotkey.

### 5. Circular import workarounds

`main.py:42` and `main.py:50` both use delayed imports with pylint disable comments:
```python
from myning.migrations import MIGRATIONS  # pylint: disable=import-outside-toplevel
from myning.tui.app import MyningApp  # pylint: disable=import-outside-toplevel
```

Delayed imports are a sign of circular dependency problems. They work but make the import graph harder to reason about.

---

## What's Working Well

- **Data-driven content.** YAML files for mines, species, upgrades, and research make it trivial to add game content without code changes. This is excellent for contributors.
- **Chapter dataclasses.** `PickArgs`, `DynamicArgs`, `AsyncArgs`, `ExitArgs`, `StoryArgs` are clean, well-named, and compose well. The pattern is easy to replicate once learned.
- **FileManager dual backend.** The JSON-to-SQLite migration path with automatic fallback is well-designed (`myning/utilities/file_manager.py`).
- **Test fixtures.** `conftest.py`'s autouse `mock_save` and `reset_objects` fixtures prevent accidental state leaks between tests. The TUI testing via Textual `Pilot` is a good pattern.
- **Consistent code style.** Black + isort enforcement means all code looks the same. No style debates.
- **BaseStore abstraction.** `myning/chapters/base_store.py` provides a clean template for store-like chapters, reducing duplication.
- **`confirm()` decorator.** `myning/utilities/pick.py` wraps handlers with Yes/No confirmation cleanly.
- **Enum usage.** `ItemType`, `PlantType`, `CharacterSpecies`, `MineType`, stat keys -- all well-defined enums that prevent magic strings.

---

## Prioritized Recommendations

### High Priority (Bug Fixes)

1. Fix `Stats.increment_float_stat` to write to `self.float_stats` (`stats.py:92`)
2. Remove duplicate `upgrades_value` in `Player.total_value` (`player.py:72`)
3. Remove debug `print()` in `Trip.from_dict` (`trip.py:111`)
4. Rename `cls` to `plant` in `Plant.from_dict` and stop shadowing `dict` built-in (`plant.py:45-49`)

### Medium Priority (Newcomer Experience)

5. Add `mypy` or `pyright` to CI -- catches bugs and documents contracts
6. Add `ruff` for linting beyond formatting
7. Make `Singleton.__call__` raise if `initialize()` hasn't been called
8. Replace `@classmethod @property` with plain class attributes before upgrading past Python 3.10
9. Move YAML loading in `config.py` into an explicit function
10. Add a `CONTRIBUTING.md` with an architecture walkthrough for newcomers

### Lower Priority (Design Improvements)

11. Make `border_title` explicit on `PickArgs` instead of inferring from module names
12. Extract garden-specific keybinding logic out of `ChapterWidget`
13. Add `pre-commit` hooks for local development
14. Consider `ruff` as a replacement for both `black` and `isort`
15. Use `yaml.safe_load()` instead of `yaml.load(f, Loader=yaml.FullLoader)`
