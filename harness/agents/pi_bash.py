"""pi-bash arm launcher.

Spawns ``pi`` (badlogic/pi-mono) with its stock recommended coding
configuration. Same subprocess shape as the Ultra arm so swapping arms in CI
is just a flag change.

Phase 0 status: subprocess wiring is in place but no model API key is used.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from ..models import TaskSpec
from .base import AgentResult


class Launcher:
    name = "pi_bash"

    def __init__(self, binary: str = "pi") -> None:
        self.binary = binary

    def run(self, task: TaskSpec, workdir: Path) -> AgentResult:
        transcript = workdir / "transcript.txt"

        # TODO(phase1): wire model API. See harness/agents/ultra.py — same deal.
        if not os.environ.get("ANTHROPIC_API_KEY"):
            transcript.write_text(
                "pi_bash arm: ANTHROPIC_API_KEY not set; skipping (Phase 0 stub).\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        if shutil.which(self.binary) is None:
            transcript.write_text(
                f"pi_bash arm: '{self.binary}' not on PATH; skipping (Phase 0 stub).\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        # TODO(phase1): containerize per task.image and apply egress allow-list.
        cmd = [self.binary]
        started = time.time()
        with transcript.open("w", encoding="utf-8") as fh:
            fh.write(f"$ {' '.join(cmd)}\n")
            fh.flush()
            try:
                proc = subprocess.run(
                    cmd,
                    input=task.prompt,
                    text=True,
                    capture_output=True,
                    timeout=task.wall_clock_seconds,
                    check=False,
                    cwd=workdir,
                )
            except subprocess.TimeoutExpired:
                fh.write("TIMEOUT\n")
                return AgentResult(transcript_path=transcript)
            fh.write(proc.stdout)
            if proc.stderr:
                fh.write("\n--- stderr ---\n")
                fh.write(proc.stderr)
            fh.write(f"\n--- exit {proc.returncode} in {time.time() - started:.2f}s ---\n")

        return AgentResult(transcript_path=transcript)
