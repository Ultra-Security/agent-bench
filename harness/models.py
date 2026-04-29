"""Dataclasses shared across the harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskSpec:
    """Parsed contents of a task directory.

    A task directory contains:

    - ``task.yaml``  : the spec parsed into this object
    - ``verify.sh``  : pass/fail script run after the agent finishes
    - ``events.yaml``: optional ground-truth events for RQ4 scoring
    """

    name: str
    path: Path
    image: str
    prompt: str
    verify_script: Path
    max_iterations: int = 25
    wall_clock_seconds: int = 1800
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    """One row of the ``runs`` table.

    Token counts are optional because the stub agent has no model behind it.
    """

    task: str
    agent: str
    started_at: float
    finished_at: float
    passed: bool
    transcript_path: Path
    tokens_in: int | None = None
    tokens_out: int | None = None

    @property
    def wall_seconds(self) -> float:
        return self.finished_at - self.started_at
