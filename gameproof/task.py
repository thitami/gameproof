"""Task definition and workspace helpers."""
from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    name: str
    description: str
    root: Path
    source_files: list[str]
    visible_tests: list[str]

    @property
    def workspace(self) -> Path:
        return self.root / "workspace"

    @property
    def hidden_tests(self) -> Path:
        return self.root / "hidden_tests"

    @property
    def golden(self) -> Path:
        return self.root / "golden"

    @classmethod
    def load(cls, root: Path) -> "Task":
        spec = json.loads((root / "task.json").read_text())
        return cls(
            name=spec["name"],
            description=spec["description"],
            root=root,
            source_files=spec["source_files"],
            visible_tests=spec["visible_tests"],
        )

    def fresh_workspace(self) -> Path:
        """Copy the pristine workspace into a temp dir the agent (or attacker) can modify."""
        dest = Path(tempfile.mkdtemp(prefix=f"gp_{self.name}_"))
        shutil.copytree(self.workspace, dest, dirs_exist_ok=True)
        return dest

    def apply_golden(self, workspace: Path) -> None:
        """Overwrite source files with the golden reference solution."""
        for rel in self.source_files:
            src = self.golden / Path(rel).name
            shutil.copy(src, workspace / rel)

    @property
    def wrong_solutions(self) -> dict[str, Path]:
        """Plausible wrong solutions (Rule 5), by name. Each replaces the single source file."""
        folder = self.root / "wrong_solutions"
        return {p.stem: p for p in sorted(folder.glob("*.py"))} if folder.is_dir() else {}

    def apply_wrong(self, workspace: Path, name: str) -> None:
        assert len(self.source_files) == 1, "wrong solutions assume one source file"
        shutil.copy(self.wrong_solutions[name], workspace / self.source_files[0])


def load_tasks(tasks_dir: Path) -> list[Task]:
    return [Task.load(p) for p in sorted(tasks_dir.iterdir()) if (p / "task.json").exists()]
