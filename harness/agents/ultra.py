"""Ultra-MCP arm launcher.

Spawns ``ultra agent`` inside the task's container image, pipes the prompt on
stdin, and captures stdout into a transcript. Token accounting will come from
the JSONL event stream emitted by the planned ``cmd/agent-bench-runner``
companion in the upstream Ultra repo.

Phase 0 status: subprocess wiring is in place but the model API is not. The
launcher supports a ``dry_run`` mode that exercises the full call shape
WITHOUT contacting any provider. Without ``dry_run``, the launcher requires
both the binary and ``ANTHROPIC_API_KEY``; if either is missing it writes a
clearly-labelled stub transcript instead of crashing.
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

    def run(
        self,
        task: TaskSpec,
        workdir: Path,
        *,
        dry_run: bool = False,
    ) -> AgentResult:
        transcript = workdir / "transcript.txt"

        # Per methodology Section 4.1, the real run shape is:
        #   ultra agent --max-iterations <N>
        # with the prompt piped on stdin and cwd=workdir. The container,
        # egress allow-list, and event-stream wiring are Phase 1 work
        # (TODO: methodology §3 container contract).
        cmd = [
            self.binary,
            "agent",
            "--max-iterations",
            str(task.max_iterations),
        ]

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

        # TODO(phase1): parse tokens from the runner's JSONL event stream
        # and surface provider rate-limit headers (cf. methodology §6 token
        # accounting requirement).
        return AgentResult(transcript_path=transcript)


def _write_dry_run_transcript(
    arm_name: str,
    cmd: list[str],
    task: TaskSpec,
    transcript: Path,
) -> AgentResult:
    """Common dry-run transcript shape across all real arms.

    The point is to prove the per-arm plumbing — task spec parsed, workdir
    created, transcript written, row inserted — without making a network
    call or requiring an API key.
    """
    transcript.write_text(
        f"# DRY RUN: {arm_name}\n"
        f"# No LLM call was made. tokens_in/tokens_out reported as 0.\n"
        f"intended cmd: {' '.join(cmd)}\n"
        f"task: {task.name}\n"
        f"max_iterations: {task.max_iterations}\n"
        f"wall_clock_seconds: {task.wall_clock_seconds}\n"
        f"image: {task.image}\n"
        f"prompt:\n{task.prompt}\n",
        encoding="utf-8",
    )
    return AgentResult(transcript_path=transcript, tokens_in=0, tokens_out=0)
