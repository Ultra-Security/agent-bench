"""Agent launchers.

Each module in this package exposes a single ``Launcher`` class implementing
``base.AgentLauncher``. The harness selects one via ``--agent``.
"""

from .base import AgentLauncher, AgentResult

__all__ = ["AgentLauncher", "AgentResult"]
