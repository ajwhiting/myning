import json
import os
import shutil
import sqlite3
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Type, TypeVar

from myning.objects.object import Object

T = TypeVar("T", bound=Object)

DB_PATH = ".data/myning.db"

# Keys that survive a reset_game() call (no file extension — these are SQLite keys)
_PROTECTED_KEYS = {"stats", "settings"}


class Subfolders(str, Enum):
    ITEMS = "items"
    ENTITIES = "entities"


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _db_exists() -> bool:
    return Path(DB_PATH).is_file()


class FileManager:
    # Kept for any callers that reference it by name
    NEVER_DELETE = ["stats.json", "settings.json"]

    @classmethod
    def setup(cls):
        if not Path(".data").is_dir():
            os.mkdir(".data")
        if _db_exists():
            # Ensure table exists (idempotent)
            with _connect() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS save_data "
                    "(key TEXT PRIMARY KEY, data TEXT NOT NULL)"
                )
        else:
            # Legacy JSON directories (kept until migration #11 runs)
            if not Path(".data/items").is_dir():
                os.mkdir(".data/items")
            if not Path(".data/entities").is_dir():
                os.mkdir(".data/entities")

    @classmethod
    def multi_save(cls, *items: Object):
        for item in items:
            cls.save(item)

    @staticmethod
    def save(item: Object):
        key = item.file_name
        data = json.dumps(item.to_dict())
        if _db_exists():
            with _connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO save_data (key, data) VALUES (?, ?)",
                    (key, data),
                )
        else:
            path = f".data/{key}.json"
            with open(path, "w") as f:
                json.dump(item.to_dict(), f, indent=2)

    @staticmethod
    def load(type: Type[T], file_name=None, subfolder="") -> T | None:
        key = f"{subfolder}/{file_name}" if subfolder else file_name

        if _db_exists():
            with _connect() as conn:
                row = conn.execute("SELECT data FROM save_data WHERE key=?", (key,)).fetchone()
            if row is not None:
                return type.from_dict(json.loads(row[0]))
            # Key not in DB yet (e.g. fresh object after migration)
            return None

        # JSON fallback (pre-migration)
        if subfolder:
            json_path = f".data/{subfolder}/{file_name}.json"
        else:
            json_path = f".data/{file_name}.json"
        if not Path(json_path).is_file():
            return None
        if os.path.getsize(json_path) == 0:
            return type()
        with open(json_path) as f:
            return type.from_dict(json.load(f))

    @staticmethod
    def delete(item: Object):
        key = item.file_name
        if _db_exists():
            with _connect() as conn:
                conn.execute("DELETE FROM save_data WHERE key=?", (key,))
        else:
            path = f".data/{key}.json"
            if Path(path).is_file():
                os.remove(path)

    @classmethod
    def multi_delete(cls, *items: Object):
        for item in items:
            cls.delete(item)

    @staticmethod
    def reset_game():
        if _db_exists():
            placeholders = ",".join("?" * len(_PROTECTED_KEYS))
            with _connect() as conn:
                conn.execute(
                    f"DELETE FROM save_data WHERE key NOT IN ({placeholders})",
                    tuple(_PROTECTED_KEYS),
                )
        else:
            # Legacy JSON reset
            for path in Path(".data/items").iterdir():
                os.remove(path)
            for path in Path(".data/entities").iterdir():
                os.remove(path)
            for path in Path(".data").iterdir():
                if path.is_file() and path.name not in FileManager.NEVER_DELETE:
                    os.remove(path)

    @staticmethod
    def backup_game():
        backup_dir = ".data.bak"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.copytree(".data", backup_dir)
