"""Migration 11: Import all JSON save files into a single SQLite database.

After this migration FileManager reads/writes exclusively from .data/myning.db.
The original JSON files are left in place as a backup; they are no longer read.
"""

import json
import sqlite3
from pathlib import Path

DB_PATH = ".data/myning.db"


def run():
    # Remove a partial DB from a previously failed run so we start clean.
    db_file = Path(DB_PATH)
    if db_file.is_file():
        db_file.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS save_data (key TEXT PRIMARY KEY, data TEXT NOT NULL)")

    data_dir = Path(".data")
    if not data_dir.is_dir():
        # Nothing to migrate (fresh install handled by setup())
        conn.commit()
        conn.close()
        return

    # Top-level JSON files: key = stem (e.g. "player", "stats")
    for json_file in data_dir.glob("*.json"):
        key = json_file.stem
        try:
            raw = json_file.read_text()
            json.loads(raw)  # validate — skip corrupt files
            conn.execute(
                "INSERT OR REPLACE INTO save_data (key, data) VALUES (?, ?)",
                (key, raw),
            )
        except (json.JSONDecodeError, OSError):
            print(f"  Warning: skipping unreadable file {json_file}")

    # Sub-directory JSON files: key = "{subdir}/{stem}" (e.g. "items/abc-123")
    for subdir in ("items", "entities"):
        subdir_path = data_dir / subdir
        if not subdir_path.is_dir():
            continue
        for json_file in subdir_path.glob("*.json"):
            key = f"{subdir}/{json_file.stem}"
            try:
                raw = json_file.read_text()
                json.loads(raw)  # validate
                conn.execute(
                    "INSERT OR REPLACE INTO save_data (key, data) VALUES (?, ?)",
                    (key, raw),
                )
            except (json.JSONDecodeError, OSError):
                print(f"  Warning: skipping unreadable file {json_file}")

    conn.commit()
    conn.close()
    print("\nSave data migrated to SQLite. JSON files kept as backup.")
