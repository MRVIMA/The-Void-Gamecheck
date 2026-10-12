"""A small SQLite cache, so repeated look-ups don't hit the public APIs again."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

DEFAULT_TTL = 24 * 3600


class Cache:
    def __init__(self, path: Path | str = ":memory:", ttl: int = DEFAULT_TTL) -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, "
                         "value TEXT NOT NULL, fetched REAL NOT NULL)")
        self._db.commit()

    def get(self, key: str):
        with self._lock:
            row = self._db.execute("SELECT value, fetched FROM cache WHERE key = ?",
                                   (key,)).fetchone()
        if row is None or time.time() - row[1] > self.ttl:
            return None
        return json.loads(row[0])

    def fetched_at(self, key: str) -> float | None:
        with self._lock:
            row = self._db.execute("SELECT fetched FROM cache WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def put(self, key: str, value) -> None:
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                             (key, json.dumps(value), time.time()))
            self._db.commit()

    def clear(self) -> None:
        with self._lock:
            self._db.execute("DELETE FROM cache")
            self._db.commit()
