"""Ultra-MCP arm launcher.

Spawns ``ultra agent`` inside the task's container image, pipes the prompt on
stdin, and captures stdout into a transcript. Token accounting will come from
the JSONL event stream emitted by the planned ``cmd/agent-bench-runner``
companion in the main ultra repo.

Phase 0 status: subprocess wiring is in place but the model API is not. The
launcher will exit cleanly with a transcript noting the missing API key — it
does NOT make any network calls.
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
    name = "ultra"

    def __init__(self, binary: str = "ultra") -> None:
        self.binary = binary

    def run(self, task: TaskSpec, workdir: Path) -> AgentResult:
        transcript = workdir / "transcript.txt"

        # TODO(phase1): wire model API. For now we require ANTHROPIC_API_KEY to
        # be present and refuse to make calls without it. The subprocess shape
        # below is the target — Phase 1 will swap the binary path for a
        # `cmd/agent-bench-runner` wrapper that emits JSONL events.
        if not os.environ.get("ANTHROPIC_API_KEY"):
            transcript.write_text(
                "ultra arm: ANTHROPIC_API_KEY not set; skipping (Phase 0 stub).\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        if shutil.which(self.binary) is None:
            transcript.write_text(
                f"ultra arm: '{self.binary}' not on PATH; skipping (Phase 0 stub).\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        # TODO(phase1): run inside the task's container image
        # (task.image) with egress allow-list per the methodology. For now we
        # just shell out to the host binary so the call shape is testable.
        cmd = [
            self.binary,
            "agent",
            "--max-iterations",
            str(task.max_iterations),
        ]
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

        # TODO(phase1): parse tokens from the runner's JSONL event stream.
        return AgentResult(transcript_path=transcript)
