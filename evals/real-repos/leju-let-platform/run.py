#!/usr/bin/env python3
"""LET-Platform wrapper: sparse-clone the backend module and run the shared runner."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "leju-robot-ota"
sys.path.insert(0, str(SHARED))
_SPEC = importlib.util.spec_from_file_location(
    "leju_ota_real_repo_run", SHARED / "run.py"
)
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)

base.SCENARIOS = HERE / "scenarios.json"
base.HIDDEN = HERE / "hidden"
base.RESULTS = HERE / "results"


def java_home() -> str:
    for key in ("JAVA17_HOME", "JAVA_HOME"):
        value = os.environ.get(key)
        if value and (Path(value) / "bin/java").is_file():
            return value
    try:
        return subprocess.check_output(
            ["/usr/libexec/java_home", "-v", "17"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def prepare_sparse(source: Path, rev: str) -> tuple[Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix="devkit-let-eval-"))
    dest = tmp / "repo"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-checkout", str(source), str(dest)],
        check=True,
        timeout=120,
    )
    subprocess.run(
        ["git", "-C", str(dest), "sparse-checkout", "init", "--cone"],
        check=True,
        timeout=60,
    )
    subprocess.run(
        ["git", "-C", str(dest), "sparse-checkout", "set",
         "projects/backend/kuavodatahubserver"],
        check=True,
        timeout=60,
    )
    subprocess.run(
        ["git", "-C", str(dest), "checkout", "--quiet", "--detach", rev],
        check=True,
        timeout=180,
    )
    return tmp, dest


def main() -> int:
    home = java_home()
    if not home:
        print("JAVA17_HOME or a Java 17 runtime is required", file=sys.stderr)
        return 2
    os.environ["JAVA_HOME"] = home
    os.environ["PATH"] = str(Path(home) / "bin") + os.pathsep + os.environ.get("PATH", "")
    base.prepare_repo = prepare_sparse
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
