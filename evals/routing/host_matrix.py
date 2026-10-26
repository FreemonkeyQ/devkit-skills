#!/usr/bin/env python3
"""Run routing prompts against a real headless Claude Code host.

This is the host-confirmation layer after the lexical matrix. It copies the
neutral sandbox fixture to a temporary directory, sends each prompt verbatim
with the repository loaded via --plugin-dir, and records actual Skill tool
calls. Tools are restricted to read-only ones; no edit, write or shell is
allowed. Results are runtime artefacts under results/.

Run one smoke case:
  python3 evals/routing/host_matrix.py --limit 1
Run the recommended 31 cases (19 positives + 12 hard negatives):
  python3 evals/routing/host_matrix.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SANDBOX = HERE / "fixtures" / "sandbox"
RESULTS = HERE / "results"
sys.path.insert(0, str(HERE))

import matrix  # noqa: E402

SKILL_RE = re.compile(r"^(?:.*:)?dv-[a-z]+$")
SKILL_ID_RE = re.compile(r"^(?:.*:)?[a-z0-9][a-z0-9-]*$")
SKILL_READ_RE = re.compile(r"/skills/(dv-[a-z]+)/SKILL\.md$")
DEVKIT_SKILLS = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}

QODER_CLI_DIR = Path.home() / ".qoder-cn" / "bin" / "qoderclicn"
# Qoder CLI inherits SDK entrypoint vars from the host session; they must be
# stripped or the child process tries to attach to this session's auth payload.
QODER_STRIP_ENV = (
    "QODER_AGENT_SDK_ENTRYPOINT",
    "QODER_SDK_AUTH_PAYLOAD_FILE",
    "QODER_AGENT_SDK_DAEMON",
    "QODER_AGENT_SDK_VERSION",
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
)


def qoder_cli_binary() -> Path:
    version_file = QODER_CLI_DIR / "version.txt"
    if version_file.is_file():
        version = version_file.read_text(encoding="utf-8").strip()
        candidate = QODER_CLI_DIR / f"qoderclicn-{version}"
        if candidate.is_file():
            return candidate
    candidates = sorted(QODER_CLI_DIR.glob("qoderclicn-*"))
    if not candidates:
        raise SystemExit(f"no qoderclicn binary under {QODER_CLI_DIR}")
    return candidates[-1]


def select_cases(data: dict, ids: list[str] | None, limit: int | None) -> list[dict]:
    cases = data["cases"]
    if ids:
        wanted = set(ids)
        selected = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in selected}
        if missing:
            raise SystemExit(f"unknown ids: {sorted(missing)}")
    else:
        seen: set[str] = set()
        selected = []
        for case in cases:
            if case["type"] == "positive" and case["primary"] not in seen:
                seen.add(case["primary"])
                selected.append(case)
        selected += [case for case in cases if case["type"] == "hard-negative"]
    if limit is not None:
        selected = selected[:limit]
    return selected


def all_skill_names(tool_input: dict) -> list[str]:
    names = []
    for key in ("skill", "command"):
        value = tool_input.get(key)
        if not isinstance(value, str):
            continue
        value = value.strip().lstrip("/")
        if SKILL_ID_RE.match(value):
            names.append(value.split(":")[-1])
    return names


def skill_names(tool_input: dict) -> list[str]:
    return [name for name in all_skill_names(tool_input) if name in DEVKIT_SKILLS]


def external_skill_names(tool_input: dict) -> list[str]:
    return [name for name in all_skill_names(tool_input) if name not in DEVKIT_SKILLS]


def parse_event(event: dict, state: dict) -> None:
    kind = event.get("type")
    if kind == "system" and event.get("subtype") == "init":
        if event.get("model"):
            state["model"] = event["model"]
    elif kind == "assistant":
        message = event.get("message", {})
        if message.get("model"):
            state["model"] = message["model"]
        if message.get("usage"):
            state["usage"] = message["usage"]
        for block in message.get("content", []):
            if block.get("type") == "text":
                state["text"].append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                name = block.get("name")
                tool_input = block.get("input") or {}
                state["tools"].append({"name": name, "input": tool_input})
                if name == "Skill":
                    found = skill_names(tool_input)
                    external = external_skill_names(tool_input)
                    if found or external:
                        state["invoked"].extend(found)
                        state["external_skills"].extend(external)
                        state["triggered_at"] = time.monotonic()
                elif name == "Read":
                    path = str(tool_input.get("file_path") or tool_input.get("path") or "")
                    match = SKILL_READ_RE.search(path)
                    if match:
                        state["read_skills"].append(match.group(1))
    elif kind == "result":
        if event.get("result"):
            state["text"].append(str(event["result"]))
        if event.get("usage"):
            state["usage"] = event["usage"]
        if event.get("modelUsage"):
            state["model_usage"] = event["modelUsage"]


def run_case(
    case: dict,
    out_dir: Path,
    timeout: int,
    grace: int,
    model: str | None,
    host: str = "claude",
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = case["prompt"]
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="devkit-route-"))
    sandbox = tmp / "repo"
    shutil.copytree(SANDBOX, sandbox)

    stdin_payload = None
    if host == "qoder":
        cmd = [
            str(qoder_cli_binary()),
            "--output-format",
            "stream-json",
            "--input-format",
            "stream-json",
            "--plugin-dir",
            str(ROOT),
            "--permission-mode",
            "dont_ask",
            "--tools",
            "Skill",
            "Read",
            "Glob",
            "Grep",
            "--strict-mcp-config",
            "--settings",
            '{"disableAllHooks": true}',
        ]
        if model:
            cmd.extend(["-m", model])
        stdin_payload = (
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    },
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    else:
        cmd = [
            "claude",
            "-p",
                prompt,
            "--plugin-dir",
            str(ROOT),
            "--permission-mode",
            "plan",
            "--output-format",
            "stream-json",
            "--verbose",
            "--allowedTools",
            "Skill",
            "Read",
            "Glob",
            "Grep",
            "--disallowedTools",
            "Write",
            "Edit",
            "MultiEdit",
            "NotebookEdit",
            "Bash",
            "Agent",
            "WebFetch",
            "WebSearch",
            "--strict-mcp-config",
            "--settings",
            '{"disableAllHooks": true}',
        ]
        if model:
            cmd.extend(["--model", model])

    if host == "qoder":
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in QODER_STRIP_ENV
        }
    else:
        env = {
            key: value for key, value in os.environ.items() if key != "CLAUDECODE"
        }
    state = {
        "text": [],
        "tools": [],
        "invoked": [],
        "external_skills": [],
        "read_skills": [],
        "model": None,
        "usage": {},
        "model_usage": {},
        "triggered_at": None,
    }
    started = time.monotonic()
    deadline = started + timeout
    timeout_hit = False
    terminated = False

    stdout_path = out_dir / "stdout.jsonl"
    stderr_path = out_dir / "stderr.txt"
    try:
        with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_file:
            proc = subprocess.Popen(
                cmd,
                cwd=sandbox,
                stdout=subprocess.PIPE,
                stderr=stderr_file,
                stdin=subprocess.PIPE if stdin_payload else subprocess.DEVNULL,
                env=env,
                bufsize=0,
                start_new_session=True,
            )
            if stdin_payload:
                assert proc.stdin is not None
                proc.stdin.write(stdin_payload.encode("utf-8"))
                proc.stdin.close()
            assert proc.stdout is not None
            fd = proc.stdout.fileno()
            buffer = ""

            def consume(line: str) -> None:
                line = line.strip()
                if not line:
                    return
                stdout_file.write(line + "\n")
                stdout_file.flush()
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    return
                parse_event(event, state)

            while True:
                now = time.monotonic()
                if now >= deadline:
                    if state["triggered_at"] is not None:
                        terminated = True
                    else:
                        timeout_hit = True
                    break
                if proc.poll() is not None:
                    remaining = os.read(fd, 65536)
                    if remaining:
                        buffer += remaining.decode("utf-8", errors="replace")
                    break
                ready, _, _ = select.select([fd], [], [], 0.5)
                if not ready:
                    continue
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    consume(line)
                    if state["triggered_at"] and not terminated:
                        deadline = min(
                            deadline, state["triggered_at"] + grace
                        )

            if buffer.strip():
                consume(buffer)

            if proc.poll() is None:
                terminated = state["triggered_at"] is not None or timeout_hit
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        proc.kill()
                    proc.wait(timeout=5)
            else:
                try:
                    while True:
                        chunk = os.read(fd, 65536)
                        if not chunk:
                            break
                        buffer += chunk.decode("utf-8", errors="replace")
                except OSError:
                    pass
                if buffer.strip():
                    consume(buffer)
            exit_code = proc.returncode
    except Exception as exc:  # infrastructure failure is recorded, not hidden
        exit_code = None
        stderr_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    duration = round(time.monotonic() - started, 1)
    invoked = state["invoked"]
    first = invoked[0] if invoked else None
    row = {
        "id": case["id"],
        "type": case["type"],
        "primary": case["primary"],
        "want": case["want"],
        "trap": case.get("trap"),
        "prompt": prompt,
        "invoked": invoked,
        "external_skills": state["external_skills"],
        "first_skill": first,
        "read_skills": state["read_skills"],
        "hit": any(name in case["want"] for name in invoked),
        "strict_hit": first in case["want"] if first else False,
        "trap_leaked": bool(case.get("trap") and case["trap"] in invoked),
        "duration_s": duration,
        "model": state["model"],
        "usage": state["usage"],
        "model_usage": state["model_usage"],
        "exit_code": exit_code,
        "timeout": timeout_hit,
        "terminated_after_trigger": terminated,
        "tools": state["tools"],
        "response": "\n".join(state["text"]).strip(),
    }
    (out_dir / "result.json").write_text(
        json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return row


def render_summary(rows: list[dict], meta: dict) -> str:
    total = len(rows)
    hits = sum(row["hit"] for row in rows)
    strict = sum(row["strict_hit"] for row in rows)
    trap = sum(row["trap_leaked"] for row in rows)
    positives = [row for row in rows if row["type"] == "positive"]
    hard = [row for row in rows if row["type"] == "hard-negative"]
    lines = [
        f"# Host routing run {meta['timestamp']} ({meta['arm']})",
        "",
        f"- host: {meta.get('host', 'claude-code')} {meta['host_version']}",
        f"- model(s): {', '.join(meta['models']) or 'unknown'}",
        f"- plugin: {meta['plugin_dir']}",
        f"- scenarios sha256: `{meta['scenarios_sha256']}`",
        f"- cases: {total}; any-hit: {hits}; strict-hit: {strict}; trap leaks: {trap}",
        f"- positives: {sum(row['hit'] for row in positives)}/{len(positives)}; "
        f"hard negatives: {sum(row['hit'] for row in hard)}/{len(hard)}",
        f"- cases with external skills: "
        f"{sum(bool(row.get('external_skills')) for row in rows)}",
        "",
        "| id | type | expected | invoked | external | hit | trap | sec | error |",
        "|---|---|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        error = ""
        if row["timeout"]:
            error = "timeout"
        elif (
            row["exit_code"] not in (0, -15, 143, None)
            and not row.get("terminated_after_trigger")
        ):
            error = f"exit {row['exit_code']}"
        lines.append(
            f"| {row['id']} | {row['type']} | {', '.join(row['want'])} | "
            f"{', '.join(row['invoked']) or '-'} | "
            f"{', '.join(row.get('external_skills', [])) or '-'} | "
            f"{'Y' if row['hit'] else 'N'} | "
            f"{'Y' if row['trap_leaked'] else '-'} | "
            f"{row['duration_s']} | {error} |"
        )
    external_rows = [row for row in rows if row.get("external_skills")]
    if external_rows:
        lines += ["", "## External skills invoked", ""]
        for row in external_rows:
            lines.append(
                f"- `{row['id']}`: {', '.join(row['external_skills'])} "
                f"(expected {', '.join(row['want'])})"
            )
    return "\n".join(lines) + "\n"


def reanalyze(run_dir: Path) -> int:
    """Recompute hit fields from saved raw tool calls without new model calls."""
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    rows = []
    for path in sorted(run_dir.glob("*/result.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        invoked = []
        external_skills = []
        read_skills = []
        for tool in row.get("tools", []):
            name = tool.get("name")
            tool_input = tool.get("input") or {}
            if name == "Skill":
                invoked.extend(skill_names(tool_input))
                external_skills.extend(external_skill_names(tool_input))
            elif name == "Read":
                path_value = str(
                    tool_input.get("file_path") or tool_input.get("path") or ""
                )
                match = SKILL_READ_RE.search(path_value)
                if match:
                    read_skills.append(match.group(1))
        first = invoked[0] if invoked else None
        timeout_s = meta.get("timeout_s", 150)
        if (
            row.get("duration_s", 0) >= timeout_s - 1
            and row.get("exit_code") not in (0, None)
        ):
            row["timeout"] = True
        elif row.get("terminated_after_trigger") and invoked:
            row["timeout"] = False
        row.update(
            {
                "invoked": invoked,
                "external_skills": external_skills,
                "first_skill": first,
                "read_skills": read_skills,
                "hit": any(name in row["want"] for name in invoked),
                "strict_hit": first in row["want"] if first else False,
                "trap_leaked": bool(
                    row.get("trap") and row["trap"] in invoked
                ),
            }
        )
        path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        rows.append(row)

    models = sorted(
        {
            model
            for row in rows
            for model in (
                [row["model"]] if row.get("model") else list(row.get("model_usage", {}).keys())
            )
            if model
        }
    )
    meta["models"] = models or meta.get("models", [])
    (run_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report = render_summary(rows, meta)
    (run_dir / "summary.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"reanalyzed {run_dir}")
    return 0


def load_rows(run_dir: Path) -> list[dict]:
    rows = []
    for path in sorted(run_dir.glob("*/result.json")):
        try:
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARN unreadable {path}: {exc}", file=sys.stderr)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*", default=None)
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="reuse a run directory, skip cases that already have result.json",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="number of concurrent host calls when running new cases",
    )
    parser.add_argument(
        "--reanalyze",
        type=Path,
        default=None,
        help="recompute hits from an existing run directory without model calls",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=150)
    parser.add_argument("--grace", type=int, default=5)
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--host",
        choices=["claude", "qoder"],
        default="claude",
        help="host CLI to drive: claude (Claude Code) or qoder (Qoder CLI CN)",
    )
    parser.add_argument("--arm", default="natural")
    parser.add_argument(
        "--explicit",
        action="store_true",
        help="prepend an instruction to use the expected skill (positive control)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.reanalyze is not None:
        return reanalyze(args.reanalyze)

    data, skills, _ = matrix.load(ROOT)
    errors = matrix.validate(data, skills)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 2
    all_cases = select_cases(data, args.ids, args.limit)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if args.resume is not None:
        out_root = args.resume
        out_root.mkdir(parents=True, exist_ok=True)
        existing = load_rows(out_root)
        done_ids = {row["id"] for row in existing}
        todo = [case for case in all_cases if case["id"] not in done_ids]
        meta_path = out_root / "meta.json"
        meta = (
            json.loads(meta_path.read_text(encoding="utf-8"))
            if meta_path.exists()
            else {}
        )
        meta.setdefault("timestamp", timestamp)
        meta.setdefault("arm", args.arm)
    else:
        existing = []
        todo = all_cases
        out_root = RESULTS / f"host-{timestamp}-{args.arm}"
        out_root.mkdir(parents=True, exist_ok=True)
        meta = {"timestamp": timestamp, "arm": args.arm}

    if args.dry_run:
        for case in todo:
            print(f"{case['id']} {case['type']} want={case['want']} {case['prompt']}")
        print(f"{len(todo)} to run, {len(existing)} existing")
        return 0

    if args.host == "qoder":
        host_binary = qoder_cli_binary()
        host_version = host_binary.name
        host_name = "qoder-cli-cn"
        permission = "dont_ask"
    else:
        host_version = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True
        ).stdout.strip()
        host_name = "claude-code"
        permission = "plan"
    meta.update(
        {
            "host": host_name,
            "host_version": host_version,
            "plugin_dir": str(ROOT),
            "sandbox": str(SANDBOX),
            "permission": permission,
            "allowed_tools": ["Skill", "Read", "Glob", "Grep"],
            "disallowed_tools": [
                "Write",
                "Edit",
                "MultiEdit",
                "NotebookEdit",
                "Bash",
                "Agent",
                "WebFetch",
                "WebSearch",
            ],
            "model_arg": args.model,
            "explicit_skill": args.explicit,
            "timeout_s": args.timeout,
            "grace_s": args.grace,
            "workers": args.workers,
            "scenarios_sha256": hashlib.sha256(
                (HERE / "scenarios.json").read_bytes()
            ).hexdigest(),
            "case_ids": [case["id"] for case in all_cases],
            "run_ids": [case["id"] for case in todo],
        }
    )

    def run_one(case: dict) -> dict:
        run_case_input = case
        if args.explicit:
            run_case_input = dict(case)
            run_case_input["prompt"] = (
                f"请使用 {case['want'][0]} 技能完成以下任务：\n\n{case['prompt']}"
            )
        return run_case(
            run_case_input,
            out_root / case["id"],
            args.timeout,
            args.grace,
            args.model,
            host=args.host,
        )

    def report(row: dict) -> None:
        print(
            f"   done {row['id']} invoked={row['invoked'] or '-'} "
            f"hit={row['hit']} read={row['read_skills'] or '-'} "
            f"{row['duration_s']}s" + (" timeout" if row["timeout"] else ""),
            flush=True,
        )

    total = len(todo)
    if total and args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_one, case): case for case in todo}
            for finished, future in enumerate(as_completed(futures), 1):
                case = futures[future]
                print(
                    f"== {finished}/{total} {case['id']} -> {case['want']}",
                    flush=True,
                )
                try:
                    report(future.result())
                except Exception as exc:
                    print(
                        f"ERROR {case['id']}: {type(exc).__name__}: {exc}",
                        file=sys.stderr,
                        flush=True,
                    )
    else:
        for index, case in enumerate(todo, 1):
            print(f"== {index}/{total} {case['id']} -> {case['want']}", flush=True)
            try:
                report(run_one(case))
            except Exception as exc:
                print(
                    f"ERROR {case['id']}: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )

    order = {case["id"]: index for index, case in enumerate(all_cases)}
    rows = sorted(
        load_rows(out_root), key=lambda row: order.get(row["id"], len(order))
    )
    models = sorted(
        {
            model
            for row in rows
            for model in (
                [row["model"]]
                if row.get("model")
                else list(row.get("model_usage", {}).keys())
            )
            if model
        }
    )
    completed_ids = {row["id"] for row in rows}
    meta["models"] = models
    meta["completed_ids"] = [row["id"] for row in rows]
    meta["missing_ids"] = [
        case["id"] for case in all_cases if case["id"] not in completed_ids
    ]
    (out_root / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_root / "summary.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_text = render_summary(rows, meta)
    (out_root / "summary.md").write_text(report_text, encoding="utf-8")
    print(report_text)
    print(f"wrote {out_root}")
    return 0 if any(row.get("model") for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
