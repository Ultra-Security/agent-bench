"""Agent launcher protocol.

Every arm (Ultra-MCP, pi-bash, pi-MCP, stub) implements ``AgentLauncher``.
The harness only ever talks to ``run`` — it never imports an arm directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models import TaskSpec


@dataclass
class AgentResult:
    """What an agent run produces, before verification."""

    transcript_path: Path
    tokens_in: int | None = None
    tokens_out: int | None = None


@runtime_checkable
class AgentLauncher(Protocol):
    """Spawns an agent against one task and returns a transcript path.

    Implementations must:

    - Be side-effect-free until ``run`` is called.
    - Write a transcript to ``workdir / "transcript.txt"`` (or .jsonl).
    - Never raise on agent-side failure; surface failure in the transcript
      and let ``verify.sh`` decide pass/fail.
    """

    name: str

    def run(self, task: TaskSpec, workdir: Path) -> AgentResult: ...
