"""pi-MCP arm launcher.

Per methodology Section 4.3, pi-MCP is pi.dev launched with
``--no-builtin-tools -e agents/pi-dev-mcp/pi-ultra-mcp.ts`` so its only tools
are the ones Ultra exposes via MCP. The extension itself spawns Ultra as a
stdio subprocess; the launcher exports ``ULTRA_BIN`` so the extension can
find it.

Phase 0 status: subprocess wiring is in place, plus ``dry_run`` mode that
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

# Path to the pi.dev extension within this repo. Resolved at import time so
# the launcher fails fast if the file moves.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXTENSION_PATH = REPO_ROOT / "agents" / "pi-dev-mcp" / "pi-ultra-mcp.ts"


class Launcher:
    name = "pi_mcp"

    def __init__(self, pi_binary: str = "pi", ultra_binary: str = "ultra") -> None:
        self.pi_binary = pi_binary
        self.ultra_binary = ultra_binary

    def run(
        self,
        task: TaskSpec,
        workdir: Path,
        *,
        dry_run: bool = False,
    ) -> AgentResult:
        transcript = workdir / "transcript.txt"

        # Per methodology Section 4.3, the launch shape is:
        #   pi --no-builtin-tools -e <extension>
        # with prompt on stdin and ULTRA_BIN env set so the extension can
        # spawn Ultra as a stdio subprocess.
        cmd = [
            self.pi_binary,
            "--no-builtin-tools",
            "-e",
            str(EXTENSION_PATH),
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

        if shutil.which(self.pi_binary) is None:
            transcript.write_text(
                f"{self.name} arm: '{self.pi_binary}' not on PATH; skipping (Phase 0 stub).\n"
                f"intended cmd: {' '.join(cmd)}\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        ultra_path = shutil.which(self.ultra_binary)
        if ultra_path is None:
            transcript.write_text(
                f"{self.name} arm: '{self.ultra_binary}' not on PATH "
                f"(needed by the pi-MCP extension to spawn Ultra over stdio); "
                f"skipping (Phase 0 stub).\n"
                f"intended cmd: {' '.join(cmd)}\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        if not EXTENSION_PATH.is_file():
            transcript.write_text(
                f"{self.name} arm: extension not found at {EXTENSION_PATH}; "
                f"skipping (Phase 0 stub).\n",
                encoding="utf-8",
            )
            return AgentResult(transcript_path=transcript)

        env = {**os.environ, "ULTRA_BIN": ultra_path}

        started = time.time()
        with transcript.open("w", encoding="utf-8") as fh:
            fh.write(f"$ ULTRA_BIN={ultra_path} {' '.join(cmd)}\n")
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
                    env=env,
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
