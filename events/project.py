"""Rebuildable SQLite read projection for an event stream."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .store import EventStore


class EventProjector:
    """Creates a disposable SQLite projection; it never modifies the JSONL source."""

    def __init__(self, event_path: str | Path, database_path: str | Path) -> None:
        self.event_path = Path(event_path)
        self.database_path = Path(database_path)

    def rebuild(self) -> int:
        """Replace the projection with the complete current event stream and return its size."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                DROP VIEW IF EXISTS v_proposals;
                DROP TABLE IF EXISTS events;
                CREATE TABLE events (
                    seq INTEGER PRIMARY KEY,
                    ts TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    round_id INTEGER,
                    strategy TEXT,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    hash TEXT NOT NULL
                );
                CREATE VIEW v_proposals AS
                    SELECT * FROM events WHERE event_type LIKE 'proposal.%';
                """
            )
            rows = [
                (
                    event["seq"], event["ts"], event["event_type"], event["round_id"],
                    event["strategy"], event["actor"], json.dumps(event["payload"], sort_keys=True),
                    event["prev_hash"], event["hash"],
                )
                for event in EventStore(self.event_path).iter_events()
            ]
            connection.executemany(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
            )
        return len(rows)

    def connect_readonly(self) -> sqlite3.Connection:
        """Open the projection in SQLite read-only mode for dashboard consumers."""
        return sqlite3.connect(f"file:{self.database_path.resolve()}?mode=ro", uri=True)
