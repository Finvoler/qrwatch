from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_DIR = ROOT / "evals" / "benchmarks"
BASELINES_DIR = ROOT / "evals" / "baselines"
RESULTS_DIR = ROOT / "evals" / "results"
QUEUE_DIR = ROOT / "runtime" / "tasks" / "queue"
RUNS_DIR = ROOT / "artifacts" / "runs"

DEFAULT_HARNESS_COMMAND = "{python} tools/harness_loop.py --once"
RUN_ID_PATTERN = re.compile(r"^Run id:\s*(?P<run_id>\S+)\s*$", re.MULTILINE)
REGRESSION_POLICIES = {"none", "fail_on_status_regression"}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def git_commit() -> str | None:
    if shutil.which("git") is None:
        return None
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def expand_command(command: str) -> str:
    python = f'"{sys.executable}"'
    return command.replace("{python}", python)


def discover_benchmarks() -> list[Path]:
    return sorted(BENCHMARKS_DIR.glob("*/benchmark.json"))


def baseline_path(suite: str) -> Path:
    return BASELINES_DIR / f"{suite}.json"


def validate_benchmark(path: Path, benchmark: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in ("id", "suite", "mode"):
        if not isinstance(benchmark.get(field), str) or not benchmark[field].strip():
            failures.append(f"{relative(path)} field `{field}` must be a non-empty string.")

    mode = benchmark.get("mode")
    if mode not in {"preview", "command"}:
        failures.append(f"{relative(path)} mode must be `preview` or `command`.")

    task_file = benchmark.get("task_file")
    if mode == "preview":
        if not isinstance(task_file, str) or not task_file.strip():
            failures.append(f"{relative(path)} preview benchmarks must include `task_file`.")
        elif not (path.parent / task_file).exists():
            failures.append(f"{relative(path)} references missing task file `{task_file}`.")

    commands = benchmark.get("commands", [])
    if not isinstance(commands, list) or not all(isinstance(command, str) and command.strip() for command in commands):
        failures.append(f"{relative(path)} field `commands` must be a list of command strings.")

    required_artifacts = benchmark.get("required_artifacts", [])
    if not isinstance(required_artifacts, list) or not all(
        isinstance(item, str) and item.strip() for item in required_artifacts
    ):
        failures.append(f"{relative(path)} field `required_artifacts` must be a list of artifact paths.")

    max_latency = benchmark.get("max_latency_seconds")
    if max_latency is not None and not isinstance(max_latency, (int, float)):
        failures.append(f"{relative(path)} field `max_latency_seconds` must be numeric when present.")

    policy = benchmark.get("regression_policy", "fail_on_status_regression")
    if policy not in REGRESSION_POLICIES:
        allowed = ", ".join(sorted(REGRESSION_POLICIES))
        failures.append(f"{relative(path)} regression_policy must be one of: {allowed}.")

    return failures


def run_command(command: str) -> dict[str, Any]:
    expanded = expand_command(command)
    started = time.perf_counter()
    completed = subprocess.run(
        expanded,
        cwd=str(ROOT),
        shell=True,
        text=True,
        capture_output=True,
        check=False,
    )
    latency = time.perf_counter() - started
    return {
        "command": command,
        "expanded_command": expanded,
        "return_code": completed.returncode,
        "latency_seconds": round(latency, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def stage_task(benchmark_path: Path, benchmark: dict[str, Any], ordinal: int) -> tuple[Path, dict[str, Any]]:
    source = benchmark_path.parent / str(benchmark["task_file"])
    task = load_json(source)
    benchmark_id = str(benchmark["id"])
    task["status"] = "queued"
    task["priority"] = -100000 + ordinal
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task["eval_benchmark"] = benchmark_id
    task.setdefault("run_ids", [])
    task.setdefault("artifacts", [])

    destination = QUEUE_DIR / f"{task['id']}.json"
    if destination.exists():
        existing = load_json(destination)
        if existing.get("eval_benchmark") != benchmark_id:
            raise RuntimeError(
                f"Refusing to overwrite existing queued task {relative(destination)}; "
                "remove or rename it before running evals."
            )

    write_json(destination, task)
    return destination, task


def cleanup_staged_task(path: Path, benchmark_id: str) -> None:
    if not path.exists():
        return
    try:
        task = load_json(path)
    except json.JSONDecodeError:
        return
    if task.get("eval_benchmark") == benchmark_id:
        path.unlink()


def run_preview_benchmark(path: Path, benchmark: dict[str, Any], ordinal: int) -> dict[str, Any]:
    benchmark_id = str(benchmark["id"])
    staged_path: Path | None = None
    harness_result: dict[str, Any] | None = None
    run_id: str | None = None
    run_dir: Path | None = None
    failures: list[str] = []

    try:
        staged_path, task = stage_task(path, benchmark, ordinal)
        harness_command = str(benchmark.get("harness_command", DEFAULT_HARNESS_COMMAND))
        harness_result = run_command(harness_command)
        match = RUN_ID_PATTERN.search(harness_result["stdout"])
        if match:
            run_id = match.group("run_id")
            run_dir = RUNS_DIR / run_id
        else:
            failures.append("Harness output did not include a run id.")

        if not harness_result["passed"]:
            failures.append(f"Harness command failed with exit code {harness_result['return_code']}.")

        if run_dir is not None:
            for artifact in benchmark.get("required_artifacts", []):
                artifact_path = run_dir / artifact
                if not artifact_path.exists():
                    failures.append(f"Missing required artifact: {relative(artifact_path)}")

            summary_path = run_dir / "summary.json"
            if summary_path.exists():
                summary = load_json(summary_path)
                if summary.get("task_id") != task.get("id"):
                    failures.append("Run summary task_id did not match the staged benchmark task.")
                if summary.get("execute") is not False:
                    failures.append("Preview benchmark unexpectedly ran in execute mode.")
            elif "summary.json" not in benchmark.get("required_artifacts", []):
                failures.append(f"Missing run summary: {relative(summary_path)}")
    except Exception as exc:  # noqa: BLE001 - eval results should preserve unexpected harness failures.
        failures.append(str(exc))
    finally:
        if staged_path is not None:
            cleanup_staged_task(staged_path, benchmark_id)

    commands = [harness_result] if harness_result is not None else []
    commands.extend(run_command(command) for command in benchmark.get("commands", []))
    for command_result in commands:
        if not command_result["passed"]:
            failures.append(f"Command failed: {command_result['command']}")

    return {
        "id": benchmark_id,
        "suite": benchmark.get("suite"),
        "mode": "preview",
        "description": benchmark.get("description", ""),
        "status": "failed" if failures else "passed",
        "failures": failures,
        "run_id": run_id,
        "run_summary": relative(run_dir / "summary.json") if run_dir is not None else None,
        "commands": commands,
    }


def run_command_benchmark(path: Path, benchmark: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    commands = [run_command(command) for command in benchmark.get("commands", [])]
    for command_result in commands:
        if not command_result["passed"]:
            failures.append(f"Command failed: {command_result['command']}")

    return {
        "id": benchmark.get("id"),
        "suite": benchmark.get("suite"),
        "mode": "command",
        "description": benchmark.get("description", ""),
        "status": "failed" if failures else "passed",
        "failures": failures,
        "definition": relative(path),
        "commands": commands,
    }


def apply_latency_policy(result: dict[str, Any], benchmark: dict[str, Any], elapsed: float) -> None:
    result["latency_seconds"] = round(elapsed, 3)
    max_latency = benchmark.get("max_latency_seconds")
    if isinstance(max_latency, (int, float)) and elapsed > max_latency:
        result.setdefault("failures", []).append(
            f"Latency {elapsed:.3f}s exceeded max_latency_seconds {max_latency}."
        )
        result["status"] = "failed"


def normalize_result_for_baseline(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": result["id"],
        "mode": result["mode"],
        "status": result["status"],
        "commands": [
            {
                "command": command["command"],
                "return_code": command["return_code"],
                "passed": command["passed"],
            }
            for command in result.get("commands", [])
        ],
    }


def build_baseline(result_doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "suite": result_doc["suite"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "commit": result_doc.get("commit"),
        "benchmarks": {
            result["id"]: normalize_result_for_baseline(result)
            for result in result_doc.get("benchmarks", [])
        },
    }


def compare_with_baseline(result_doc: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    baseline_benchmarks = baseline.get("benchmarks", {})
    if not isinstance(baseline_benchmarks, dict):
        return ["Baseline field `benchmarks` must be an object keyed by benchmark id."]

    for result in result_doc.get("benchmarks", []):
        policy = result.get("regression_policy", "fail_on_status_regression")
        if policy == "none":
            continue

        benchmark_id = result["id"]
        expected = baseline_benchmarks.get(benchmark_id)
        if not isinstance(expected, dict):
            failures.append(f"No baseline entry for benchmark `{benchmark_id}`.")
            continue

        if expected.get("mode") != result.get("mode"):
            failures.append(
                f"Benchmark `{benchmark_id}` mode changed from `{expected.get('mode')}` to `{result.get('mode')}`."
            )

        expected_status = expected.get("status")
        current_status = result.get("status")
        if expected_status == "passed" and current_status != "passed":
            failures.append(
                f"Benchmark `{benchmark_id}` regressed from baseline status `passed` to `{current_status}`."
            )

    return failures


def apply_baseline_policy(
    *,
    result_doc: dict[str, Any],
    compare_baseline: bool,
    update_baseline: bool,
) -> list[str]:
    path = baseline_path(str(result_doc["suite"]))
    result_doc["baseline"] = {
        "path": relative(path),
        "compared": False,
        "updated": False,
    }

    failures: list[str] = []
    if update_baseline:
        if result_doc["status"] != "passed":
            failures.append("Refusing to update baseline because the eval suite did not pass.")
        else:
            write_json(path, build_baseline(result_doc))
            result_doc["baseline"]["updated"] = True
        return failures

    if not compare_baseline:
        return failures

    result_doc["baseline"]["compared"] = True
    if not path.exists():
        failures.append(f"Missing baseline file: {relative(path)}. Run with --update-baseline after a known-good pass.")
        return failures

    try:
        baseline = load_json(path)
    except json.JSONDecodeError as exc:
        failures.append(f"Baseline file is not valid JSON: {exc}")
        return failures

    if baseline.get("suite") != result_doc["suite"]:
        failures.append(
            f"Baseline suite `{baseline.get('suite')}` does not match current suite `{result_doc['suite']}`."
        )
        return failures

    failures.extend(compare_with_baseline(result_doc, baseline))
    return failures


def run_benchmark(path: Path, ordinal: int) -> dict[str, Any]:
    benchmark = load_json(path)
    failures = validate_benchmark(path, benchmark)
    if failures:
        return {
            "id": benchmark.get("id", path.parent.name),
            "suite": benchmark.get("suite"),
            "mode": benchmark.get("mode"),
            "definition": relative(path),
            "status": "failed",
            "failures": failures,
            "commands": [],
        }

    started = time.perf_counter()
    if benchmark["mode"] == "preview":
        result = run_preview_benchmark(path, benchmark, ordinal)
    else:
        result = run_command_benchmark(path, benchmark)
    apply_latency_policy(result, benchmark, time.perf_counter() - started)
    result["definition"] = relative(path)
    result["cost"] = None
    result["model_config"] = benchmark.get("model_config")
    result["regression_policy"] = benchmark.get("regression_policy", "fail_on_status_regression")
    return result


def print_benchmark_list(paths: list[Path]) -> None:
    for path in paths:
        benchmark = load_json(path)
        print(f"{benchmark.get('suite', 'unknown')}\t{benchmark.get('id', path.parent.name)}\t{relative(path)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run harness evaluation benchmarks.")
    parser.add_argument("--suite", default="smoke", help="Benchmark suite to run.")
    parser.add_argument("--benchmark", help="Run one benchmark id.")
    parser.add_argument("--list", action="store_true", help="List available benchmarks.")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Replace the suite baseline after a passing run.",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Skip baseline regression comparison for this run.",
    )
    args = parser.parse_args(argv)
    if args.update_baseline and args.no_baseline:
        parser.error("--update-baseline cannot be combined with --no-baseline")

    all_paths = discover_benchmarks()
    if args.list:
        print_benchmark_list(all_paths)
        return 0

    selected_paths = []
    for path in all_paths:
        benchmark = load_json(path)
        if benchmark.get("suite") != args.suite:
            continue
        if args.benchmark and benchmark.get("id") != args.benchmark:
            continue
        selected_paths.append(path)

    if not selected_paths:
        print(f"No benchmarks matched suite={args.suite!r} benchmark={args.benchmark!r}.")
        return 1

    started = time.perf_counter()
    results = [run_benchmark(path, index) for index, path in enumerate(selected_paths)]
    status = "passed" if all(result["status"] == "passed" for result in results) else "failed"
    result_doc = {
        "id": f"{utc_stamp()}-{args.suite}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "suite": args.suite,
        "status": status,
        "commit": git_commit(),
        "latency_seconds": round(time.perf_counter() - started, 3),
        "cost": None,
        "benchmarks": results,
    }

    baseline_failures = apply_baseline_policy(
        result_doc=result_doc,
        compare_baseline=not args.no_baseline,
        update_baseline=args.update_baseline,
    )
    if baseline_failures:
        result_doc["status"] = "failed"
        result_doc["baseline"]["failures"] = baseline_failures

    result_path = RESULTS_DIR / f"{result_doc['id']}.json"
    write_json(result_path, result_doc)

    for result in results:
        print(f"{result['id']}: {result['status']} ({result['latency_seconds']}s)")
        for failure in result.get("failures", []):
            print(f"  - {failure}")
    for failure in baseline_failures:
        print(f"baseline: failed - {failure}")
    if result_doc["baseline"]["updated"]:
        print(f"Baseline updated: {result_doc['baseline']['path']}")
    elif result_doc["baseline"]["compared"]:
        print(f"Baseline compared: {result_doc['baseline']['path']}")
    print(f"Eval result: {relative(result_path)}")

    return 0 if result_doc["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
