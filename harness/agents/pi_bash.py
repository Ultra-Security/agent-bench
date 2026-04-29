"""pi-bash arm launcher.

Spawns ``pi`` (badlogic/pi-mono) with its stock recommended coding
configuration. Same subprocess shape as the Ultra arm so swapping arms in CI
is just a flag change.

Phase 0 status: subprocess wiring is in place, plus a ``dry_run`` mode that
exercises the call shape without any model API call (no key required).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from ..models import TaskSpec
from .base import AgentResult
from .ultra import _write_dry_run_transcript


class Launcher:
    name = "pi_bash"

    def __init__(self, binary: str = "pi") -> None:
        self.binary = binary

    def run(
        self,
        task: TaskSpec,
        workdir: Path,
        *,
        dry_run: bool = False,
    ) -> AgentResult:
        transcript = workdir / "transcript.txt"

        # Per methodology Section 4.2, pi-bash uses pi.dev's stock
        # recommended coding configuration — no flags, no extensions.
        # TODO(phase1): containerize per task.image and apply egress
        # allow-list (methodology §3).
        cmd = [self.binary]

        if dry_run:
            return _write_dry_run_transcript(self.name, cmd, task, transcript)

        if not os.environ.get("ANTHROPIC_API_KEY"):
            transcript.write_text(
                f"{self.name} arm: ANTHROPIC_API_KEY not set; skipping (Phase 0 stub).\n"
                f"intended cmd: {' '.join(cmd)}\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        if shutil.which(self.binary) is None:
            transcript.write_text(
                f"{self.name} arm: '{self.binary}' not on PATH; skipping (Phase 0 stub).\n"
                f"intended cmd: {' '.join(cmd)}\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

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

        # TODO(phase1): parse tokens from pi.dev's transcript / provider
        # rate-limit headers (methodology §6).
        return AgentResult(transcript_path=transcript)
