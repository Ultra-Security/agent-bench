"""Harness entry point.

    python -m harness.run tasks/sanity --agent stub

Loads a task spec, spawns the chosen agent, runs the task's ``verify.sh``,
and writes a row to ``results/runs.sqlite``. Exit code mirrors verify.sh:
0 on pass, non-zero on fail.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

from .agents.base import AgentLauncher, AgentResult
from .models import RunResult, TaskSpec
from .storage import RunStore

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "results" / "runs.sqlite"

KNOWN_AGENTS = {
    "stub": "harness.agents.stub",
    "ultra": "harness.agents.ultra",
    "pi_bash": "harness.agents.pi_bash",
    "pi_mcp": "harness.agents.pi_mcp",
}


def load_task(task_dir: Path) -> TaskSpec:
    """Parse ``task.yaml`` + sibling ``verify.sh`` into a TaskSpec."""
    task_dir = task_dir.resolve()
    spec_path = task_dir / "task.yaml"
    verify_path = task_dir / "verify.sh"
    if not spec_path.is_file():
        raise FileNotFoundError(f"missing task.yaml in {task_dir}")
    if not verify_path.is_file():
        raise FileNotFoundError(f"missing verify.sh in {task_dir}")

    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    return TaskSpec(
        name=str(raw.get("name", task_dir.name)),
        path=task_dir,
        image=str(raw.get("image", "python:3.12-slim")),
        prompt=str(raw.get("prompt", "")),
        verify_script=verify_path,
        max_iterations=int(raw.get("max_iterations", 25)),
        wall_clock_seconds=int(raw.get("wall_clock_seconds", 1800)),
        raw=raw,
    )


def load_agent(name: str) -> AgentLauncher:
    """Instantiate an agent launcher by name."""
    if name not in KNOWN_AGENTS:
        raise ValueError(f"unknown agent {name!r}; pick one of {sorted(KNOWN_AGENTS)}")
    module = importlib.import_module(KNOWN_AGENTS[name])
    launcher = module.Launcher()
    if not isinstance(launcher, AgentLauncher):
        raise TypeError(f"{module.__name__}.Launcher does not satisfy AgentLauncher")
    return launcher


def _run_agent(
    agent: AgentLauncher, task: TaskSpec, workdir: Path, *, dry_run: bool
) -> AgentResult:
    """Invoke the launcher, passing ``dry_run`` only if it accepts it.

    The ``AgentLauncher`` Protocol's ``run`` signature does not include
    ``dry_run`` so the stub agent stays a one-arg implementation. Real arms
    opt in by accepting the keyword.
    """
    import inspect

    sig = inspect.signature(agent.run)
    if "dry_run" in sig.parameters:
        return agent.run(task, workdir, dry_run=dry_run)
    return agent.run(task, workdir)


def run_verify(task: TaskSpec, workdir: Path) -> bool:
    """Run ``verify.sh`` from the workdir and return True on exit 0."""
    script = task.verify_script
    cmd = ["bash", str(script)]
    proc = subprocess.run(
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
        timeout=task.wall_clock_seconds,
    )
    (workdir / "verify.stdout").write_text(proc.stdout, encoding="utf-8")
    (workdir / "verify.stderr").write_text(proc.stderr, encoding="utf-8")
    return proc.returncode == 0


def execute(
    task_dir: Path,
    agent_name: str,
    *,
    db_path: Path = DEFAULT_DB,
    workdir: Path | None = None,
    dry_run: bool = False,
) -> RunResult:
    """One full task run. Returns the persisted result.

    When ``dry_run`` is True, real arms (ultra/pi_bash/pi_mcp) skip the LLM
    call but still go through the launcher's subprocess shape. The verify
    step still runs — for tasks the agent didn't actually solve, the row
    will record ``passed=False``, which is the point: it proves the
    per-arm plumbing without burning any API budget.
    """
    task = load_task(task_dir)
    agent = load_agent(agent_name)

    if workdir is None:
        ts = int(time.time())
        suffix = "-dry" if dry_run else ""
        # Slashes in task names (e.g. terminal-bench/hello-world) would
        # otherwise create unintended directory levels under transcripts/.
        safe_name = task.name.replace("/", "_")
        workdir = (
            REPO_ROOT / "results" / "transcripts" / f"{safe_name}-{agent_name}{suffix}-{ts}"
        )
    workdir.mkdir(parents=True, exist_ok=True)

    # If the task ships a `seed/` directory, copy its contents into the
    # workdir before the agent starts. This is the canonical way for a
    # task to provide initial fixture files; agents see them at the root
    # of the workdir as if they were checked into a project. A task
    # without `seed/` simply starts in an empty workdir.
    seed_dir = task.path / "seed"
    if seed_dir.is_dir():
        for child in seed_dir.iterdir():
            dest = workdir / child.name
            if child.is_dir():
                shutil.copytree(child, dest, dirs_exist_ok=True, symlinks=True)
            else:
                shutil.copy2(child, dest)
        # Some tasks ship a `_setup.sh` that needs to run after the seed
        # is copied (e.g., to materialize a git repo from a fixture).
        # The script runs from the workdir; non-zero exit aborts the run.
        setup = workdir / "_setup.sh"
        if setup.is_file():
            subprocess.run(
                ["bash", str(setup)], cwd=workdir, check=True
            )
            setup.unlink()

    started = time.time()
    agent_result = _run_agent(agent, task, workdir, dry_run=dry_run)
    passed = run_verify(task, workdir)
    finished = time.time()

    result = RunResult(
        task=task.name,
        agent=agent_name,
        started_at=started,
        finished_at=finished,
        passed=passed,
        transcript_path=agent_result.transcript_path,
        tokens_in=agent_result.tokens_in,
        tokens_out=agent_result.tokens_out,
    )
    with RunStore(db_path) as store:
        store.insert(result)
    return result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-bench", description=__doc__)
    p.add_argument("task", type=Path, help="path to a task directory")
    p.add_argument(
        "--agent",
        choices=sorted(KNOWN_AGENTS),
        default="stub",
        help="which arm to run (default: stub)",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"sqlite path (default: {DEFAULT_DB.relative_to(REPO_ROOT)})",
    )
    p.add_argument(
        "--keep-workdir",
        action="store_true",
        help="do not clean up the per-run workdir on success",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "skip the LLM call but still go through each arm's subprocess "
            "shape and write a row. Proves wiring without burning API budget."
        ),
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = execute(args.task, args.agent, db_path=args.db, dry_run=args.dry_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"{result.task} [{result.agent}] "
        f"{'PASS' if result.passed else 'FAIL'} "
        f"in {result.wall_seconds:.2f}s "
        f"-> {result.transcript_path}"
    )
    if result.passed and not args.keep_workdir:
        # Keep transcripts around even on pass — they're cheap and the whole
        # point of the exercise is reproducibility. shutil import retained
        # for future cleanup work.
        _ = shutil
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
