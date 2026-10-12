"""Run every task x attack under every verifier and print a results matrix.

Usage:
    python -m gameproof.runner [tasks_dir]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from .attacks import ATTACKS
from .task import load_tasks
from .verifiers import HardenedVerifierV1, IsolatedVerifier, NaiveVerifier

VERIFIERS = [NaiveVerifier(), HardenedVerifierV1(), IsolatedVerifier()]
WRONG = "wrong:"  # scenario prefix for a task's wrong_solutions/<name>.py


def run(tasks_dir: Path) -> list[dict]:
    results = []
    for task in load_tasks(tasks_dir):
        scenarios = {"golden": None, "unmodified": None,
                     **{f"{WRONG}{n}": None for n in task.wrong_solutions}, **ATTACKS}
        for scenario, attack in scenarios.items():
            ws = task.fresh_workspace()
            try:
                if scenario == "golden":
                    task.apply_golden(ws)
                elif scenario.startswith(WRONG):
                    task.apply_wrong(ws, scenario[len(WRONG):])
                elif attack is not None:
                    attack(task, ws)
                row = {"task": task.name, "scenario": scenario}
                for v in VERIFIERS:
                    verdict = v.verify(task, ws)
                    row[v.name] = verdict.passed
                    row[f"{v.name}_reasons"] = verdict.reasons
                    row[f"{v.name}_checks"] = verdict.checks
                results.append(row)
            finally:
                shutil.rmtree(ws, ignore_errors=True)
    return results


def summarise(results: list[dict]) -> None:
    names = [v.name for v in VERIFIERS]
    w = max([22] + [len(r["task"]) + 2 for r in results])
    sw = max([22] + [len(r["scenario"]) + 2 for r in results])
    vw = max(len(n) for n in names) + 3
    print(f"\n{'task':<{w}}{'scenario':<{sw}}" + "".join(f"{n:<{vw}}" for n in names))
    print("-" * (w + sw + vw * len(names)))
    mark = lambda ok: "PASS" if ok else "fail"
    for r in results:
        print(f"{r['task']:<{w}}{r['scenario']:<{sw}}" + "".join(f"{mark(r[n]):<{vw}}" for n in names))

    attacks = [r for r in results if r["scenario"] in ATTACKS]
    if attacks:
        print()
        for n in names:
            print(f"Exploits accepted by {n + ' verifier:':<22} {sum(r[n] for r in attacks)}/{len(attacks)}")

    # Sanity: each wrong solution passes the visible tests (the naive verifier runs exactly
    # those) and is rejected by both hardened verifiers.
    wrong = [r for r in results if r["scenario"].startswith(WRONG)]
    if wrong:
        ok = [r for r in wrong if r["naive"] and not r["hardened_v1"] and not r["isolated"]]
        print(f"\nSanity, wrong solutions (pass visible, rejected by hardened_v1 and isolated): "
              f"{len(ok)}/{len(wrong)}")

    # Which checks ran where, per verifier (same for every scenario of a task).
    print("\nHow checks ran (from the golden scenario):")
    for r in results:
        if r["scenario"] == "golden":
            for n in names:
                flags = "; ".join(f"{k}: {v}" for k, v in r[f"{n}_checks"].items())
                print(f"  {r['task']:<{w}}{n:<{vw}}{flags}")

    # Sanity: a verifier is useless if it rejects the real solution.
    for r in results:
        for n in names:
            if r["scenario"] == "golden" and not r[n]:
                print(f"\nWARNING: golden solution rejected by {n} on {r['task']}: {r[f'{n}_reasons']}")
            if r["scenario"] == "unmodified" and r[n]:
                print(f"\nWARNING: unsolved task passes {n} on {r['task']}")
        if r["scenario"].startswith(WRONG):
            if not r["naive"]:
                print(f"\nWARNING: {r['scenario']} fails the visible tests on {r['task']}: {r['naive_reasons']}")
            for n in ("hardened_v1", "isolated"):
                if r[n]:
                    print(f"\nWARNING: {r['scenario']} accepted by {n} on {r['task']}")


def main() -> None:
    tasks_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "tasks"
    results = run(tasks_dir)
    summarise(results)
    out = Path("results.json")
    out.write_text(json.dumps(results, indent=2))
    print(f"\nFull results written to {out}")


if __name__ == "__main__":
    main()
