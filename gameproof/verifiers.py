"""Verifiers.

NaiveVerifier: runs the tests inside the agent's workspace and trusts the exit code.
This is how many environments are graded, and it is easy to game.

HardenedVerifierV1: assumes the workspace is hostile. It
  1. checks the visible tests and config files were not tampered with,
  2. copies ONLY the declared source files into a clean directory,
  3. restores pristine visible tests and adds hidden tests the agent never saw,
  4. requires every test to actually run and pass (no skips, no xfails).
Known leak: the hidden tests sit next to the submission in the clean room and run
in the same process, so the submission can read them and answer from them.

IsolatedVerifier: V1's tamper checks and a clean-room run of the visible tests,
but hidden checks run as data. Each task's hidden_cases.json stays in the parent;
a subprocess in a temp dir holding only the declared sources gets the function
names and args on stdin (never the expected values) and returns results on stdout.
The parent compares them strictly: exact type and equal value, or the exact
exception type, plus any time budget and args-unchanged check.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .task import Task

# Files that can silently change how pytest behaves.
CONFIG_FILES = ("conftest.py", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml", "sitecustomize.py")


@dataclass
class Verdict:
    passed: bool
    reasons: list[str] = field(default_factory=list)
    # How each group of checks ran, e.g. {"hidden cases (7)": "isolated subprocess"}.
    checks: dict[str, str] = field(default_factory=dict)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_pytest(cwd: Path, test_paths: list[str]) -> tuple[int, dict]:
    """Run pytest and return (exit_code, counts) parsed from a JUnit report."""
    report = cwd / ".gp_report.xml"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         f"--junitxml={report}", *test_paths],
        cwd=cwd, capture_output=True, text=True, timeout=120,
    )
    counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    if report.exists():
        root = ET.parse(report).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        if suite is not None:
            for key in counts:
                counts[key] = int(suite.get(key, 0))
    return proc.returncode, counts


class NaiveVerifier:
    name = "naive"

    def verify(self, task: Task, workspace: Path) -> Verdict:
        code, _ = _run_pytest(workspace, ["tests"])
        return Verdict(passed=code == 0, reasons=[] if code == 0 else [f"pytest exit code {code}"],
                       checks={"visible tests": "workspace pytest"})


def _tamper_checks(task: Task, workspace: Path) -> list[str]:
    """Visible tests must be byte-identical and no new config/hook files may appear."""
    reasons: list[str] = []
    for rel in task.visible_tests:
        submitted = workspace / rel
        if not submitted.exists():
            reasons.append(f"visible test deleted: {rel}")
        elif _sha256(submitted) != _sha256(task.workspace / rel):
            reasons.append(f"visible test modified: {rel}")

    for cfg in CONFIG_FILES:
        for found in workspace.rglob(cfg):
            original = task.workspace / found.relative_to(workspace)
            if not original.exists():
                reasons.append(f"unexpected config file added: {found.relative_to(workspace)}")
    return reasons


def _copy_sources(task: Task, workspace: Path, dest_root: Path) -> None:
    """Copy only the declared source files, with package __init__ files."""
    for rel in task.source_files:
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(workspace / rel, dest)
        (dest.parent / "__init__.py").touch(exist_ok=True)


def _clean_room_pytest(task: Task, workspace: Path, extra: dict[str, Path]) -> list[str]:
    """Run pristine visible tests plus `extra` test dirs against the declared sources only."""
    reasons: list[str] = []
    clean = Path(tempfile.mkdtemp(prefix="gp_clean_"))
    try:
        _copy_sources(task, workspace, clean)
        shutil.copytree(task.workspace / "tests", clean / "tests")
        for name, src in extra.items():
            shutil.copytree(src, clean / name)

        code, counts = _run_pytest(clean, ["tests", *extra])

        # Everything must actually run and pass.
        if code != 0:
            reasons.append(f"clean-room pytest exit code {code} "
                           f"(failures={counts['failures']}, errors={counts['errors']})")
        if counts["skipped"]:
            reasons.append(f"{counts['skipped']} test(s) skipped")
        if counts["tests"] == 0:
            reasons.append("no tests collected")
    finally:
        shutil.rmtree(clean, ignore_errors=True)
    return reasons


class HardenedVerifierV1:
    name = "hardened_v1"

    def verify(self, task: Task, workspace: Path) -> Verdict:
        reasons = _tamper_checks(task, workspace)
        reasons += _clean_room_pytest(task, workspace, {"hidden_tests": task.hidden_tests})
        return Verdict(passed=not reasons, reasons=reasons, checks={
            "visible tests": "clean-room pytest",
            "hidden tests": "clean-room pytest (same process and directory as submission)",
        })


# Interpreter for the case subprocess: the base Python, not the venv inside the repo,
# so sys.prefix and sys.executable don't point the submission at the task files.
_ISOLATED_PYTHON = getattr(sys, "_base_executable", None) or sys.executable
_CASE_RUNNER = (Path(__file__).parent / "case_runner.py").read_text()
_CASE_TIMEOUT = 120


def _encode(v) -> dict:
    """Must match case_runner.encode."""
    t = type(v)
    if v is None:
        return {"t": "NoneType"}
    if t in (bool, int, float, str):
        return {"t": t.__name__, "v": v}
    if t in (list, tuple):
        return {"t": t.__name__, "v": [_encode(x) for x in v]}
    if t in (set, frozenset):
        return {"t": t.__name__, "v": sorted((_encode(x) for x in v), key=json.dumps)}
    if t is dict:
        return {"t": "dict", "v": sorted(([_encode(k), _encode(x)] for k, x in v.items()), key=json.dumps)}
    raise TypeError(f"hidden case uses unsupported type {t.__name__}")


def _describe(e: dict) -> str:
    return e["t"] if e.get("unsupported") else f"{e['t']} {e.get('v')!r}"[:80]


class IsolatedVerifier:
    """Hidden checks as data, run in a separate process that never sees expected values.

    hidden_cases.json: {"cases": [{"name", "function", "args", "expected" | "raises",
    "time_limit"?, "args_unchanged"?}]}, with args (a list of positional arguments)
    and expected written as Python literals. Hidden tests that can't be expressed as
    data go in the task's hidden_pytest/ and run in the clean room like V1, flagged
    as not isolated.
    """
    name = "isolated"

    def verify(self, task: Task, workspace: Path) -> Verdict:
        reasons = _tamper_checks(task, workspace)
        checks = {"visible tests": "clean-room pytest"}

        extra = {}
        fallback = task.root / "hidden_pytest"
        if fallback.is_dir():
            extra["hidden_pytest"] = fallback
            checks["hidden pytest fallback"] = "clean-room pytest (not isolated)"
        reasons += _clean_room_pytest(task, workspace, extra)

        cases = json.loads((task.root / "hidden_cases.json").read_text())["cases"]
        checks[f"hidden cases ({len(cases)})"] = "isolated subprocess"
        reasons += self._run_cases(task, workspace, cases)
        return Verdict(passed=not reasons, reasons=reasons, checks=checks)

    def _run_cases(self, task: Task, workspace: Path, cases: list[dict]) -> list[str]:
        request = {
            "modules": [Path(rel).with_suffix("").as_posix().replace("/", ".") for rel in task.source_files],
            "cases": [{"function": c["function"], "args": [_encode(a) for a in ast.literal_eval(c["args"])]}
                      for c in cases],
        }
        box = Path(tempfile.mkdtemp(prefix="gp_box_"))
        try:
            _copy_sources(task, workspace, box)
            proc = subprocess.run(
                [_ISOLATED_PYTHON, "-I", "-c", _CASE_RUNNER],
                input=json.dumps(request), cwd=box, capture_output=True, text=True,
                timeout=_CASE_TIMEOUT, env={"PATH": os.defpath},
            )
        except subprocess.TimeoutExpired:
            return [f"hidden cases timed out after {_CASE_TIMEOUT}s"]
        finally:
            shutil.rmtree(box, ignore_errors=True)

        try:
            results = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return [f"case runner gave no results (exit {proc.returncode}): {proc.stderr.strip()[-200:]}"]
        if isinstance(results, dict):
            return [f"submission failed to import: {results.get('import_error')}"]
        if len(results) != len(cases):
            return [f"case runner returned {len(results)} results for {len(cases)} cases"]

        reasons = []
        for sent, case, got in zip(request["cases"], cases, results):
            label = f"hidden case {case['name']}"
            if "raises" in case:
                if got.get("raised") != case["raises"]:
                    outcome = f"raised {got['raised']}" if "raised" in got else f"returned {_describe(got['result'])}"
                    reasons.append(f"{label}: expected {case['raises']}, {outcome}")
                    continue
            else:
                want = _encode(ast.literal_eval(case["expected"]))
                if "raised" in got:
                    reasons.append(f"{label}: raised {got['raised']}")
                    continue
                if got["result"] != want:
                    reasons.append(f"{label}: expected {_describe(want)}, got {_describe(got['result'])}")
                    continue
            if "time_limit" in case and got["elapsed"] > case["time_limit"]:
                reasons.append(f"{label}: took {got['elapsed']:.3f}s, budget {case['time_limit']}s")
            if case.get("args_unchanged") and got["args_after"] != sent["args"]:
                reasons.append(f"{label}: mutated its arguments")
        return reasons
