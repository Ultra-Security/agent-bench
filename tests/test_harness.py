"""End-to-end harness tests using the stub agent.

These tests must pass without any LLM API key, container runtime, or
network access — they're the gate that protects Phase 0 from rotting.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from harness import run as harness_run
from harness.models import RunResult, TaskSpec
from harness.storage import RunStore

REPO_ROOT = Path(__file__).resolve().parent.parent
SANITY_TASK = REPO_ROOT / "tasks" / "sanity"


def test_load_task_reads_yaml(tmp_path: Path) -> None:
    spec = harness_run.load_task(SANITY_TASK)
    assert isinstance(spec, TaskSpec)
    assert spec.name == "sanity"
    assert "done" in spec.prompt.lower()
    assert spec.verify_script.name == "verify.sh"


def test_load_task_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        harness_run.load_task(tmp_path / "nope")


def test_load_agent_unknown() -> None:
    with pytest.raises(ValueError):
        harness_run.load_agent("does-not-exist")


@pytest.mark.parametrize("agent_name", ["stub", "ultra", "pi_bash", "pi_mcp"])
def test_load_agent_known(agent_name: str) -> None:
    launcher = harness_run.load_agent(agent_name)
    assert launcher.name == agent_name


def test_sanity_run_with_stub(tmp_path: Path) -> None:
    db = tmp_path / "runs.sqlite"
    workdir = tmp_path / "workdir"
    result = harness_run.execute(
        SANITY_TASK, "stub", db_path=db, workdir=workdir
    )
    assert isinstance(result, RunResult)
    assert result.passed is True
    assert result.task == "sanity"
    assert result.agent == "stub"
    assert result.transcript_path.exists()

    # And the row landed in sqlite.
    conn = sqlite3.connect(db)
    rows = list(conn.execute("SELECT task, agent, passed FROM runs"))
    conn.close()
    assert rows == [("sanity", "stub", 1)]


def test_run_store_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "runs.sqlite"
    with RunStore(db) as store:
        rid = store.insert(
            RunResult(
                task="t",
                agent="stub",
                started_at=1.0,
                finished_at=2.5,
                passed=True,
                transcript_path=tmp_path / "t.txt",
                tokens_in=10,
                tokens_out=20,
            )
        )
        assert rid >= 1
        rows = list(store.all())
    assert len(rows) == 1
    assert rows[0]["wall_seconds"] == pytest.approx(1.5)
