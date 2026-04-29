"""pi-MCP arm launcher.

Per methodology Section 4.3, pi-MCP is pi.dev launched with
``--no-builtin-tools -e ./pi-ultra-mcp.ts`` so its only tools are the ones
Ultra exposes via MCP.

Phase 0 status: stubbed pending the pi-MCP extension. For now this
delegates to ``pi_bash`` so the harness can still enumerate the arm.
"""

from __future__ import annotations

from pathlib import Path

from ..models import TaskSpec
from .base import AgentResult
from .pi_bash import Launcher as PiBashLauncher


class Launcher:
    name = "pi_mcp"

    def __init__(self) -> None:
        # TODO: replace with a real launcher that invokes
        #   pi --no-builtin-tools -e agents/pi-dev-mcp/pi-ultra-mcp.ts
        # once the extension exists.
        self._inner = PiBashLauncher()

    def run(self, task: TaskSpec, workdir: Path) -> AgentResult:
        return self._inner.run(task, workdir)
