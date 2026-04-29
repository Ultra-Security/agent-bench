"""SQLite persistence for run rows.

One row per (task, agent, timestamp). Schema is intentionally narrow — Phase 1
will add per-tool-call event tables once the JSONL event stream lands.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from ..models import RunResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task            TEXT    NOT NULL,
    agent           TEXT    NOT NULL,
    started_at      REAL    NOT NULL,
    finished_at     REAL    NOT NULL,
    passed          INTEGER NOT NULL,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    wall_seconds    REAL    NOT NULL,
    transcript_path TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_task_agent ON runs(task, agent);
"""


class RunStore:
    """Thin wrapper over a sqlite3 connection."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def insert(self, result: RunResult) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO runs (
                task, agent, started_at, finished_at, passed,
                tokens_in, tokens_out, wall_seconds, transcript_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.task,
                result.agent,
                result.started_at,
                result.finished_at,
                int(result.passed),
                result.tokens_in,
                result.tokens_out,
                result.wall_seconds,
                str(result.transcript_path),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def all(self) -> Iterator[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        yield from self._conn.execute("SELECT * FROM runs ORDER BY id")

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> RunStore:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
