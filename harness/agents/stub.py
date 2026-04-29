"""Stub agent — always succeeds, no LLM calls.

Used by CI and the sanity task to verify the harness end-to-end without
needing an API key or a container runtime.
"""

from __future__ import annotations

from pathlib import Path

from ..models import TaskSpec
from .base import AgentResult


class Launcher:
    name = "stub"

    def run(self, task: TaskSpec, workdir: Path) -> AgentResult:
        transcript = workdir / "transcript.txt"
        transcript.write_text(
            f"stub agent\ntask: {task.name}\nprompt: {task.prompt}\nresponse: done\n",
            encoding="utf-8",
        )
        return AgentResult(transcript_path=transcript, tokens_in=0, tokens_out=0)
