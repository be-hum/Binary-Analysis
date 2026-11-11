"""analyzer 컨테이너에서 평가 대상 에이전트(claude -p)를 한 번 이상 실행하고 runs/<run_id>/ 에 기록한다.

usage (WSL/리눅스, 프로젝트 루트에서. Windows 에서도 동작):
    python harness/run_task.py 10400 --condition baseline --k 3

runs/<run_id>/
    transcript.jsonl   claude stream-json 전체 (도구 호출·결과 포함)
    answer.json        structured output (스키마를 통과한 답안). 없으면 생략
    meta.json          상태, 시간, 토큰, 도구 호출 수, 조건, 대상 바이너리 sha256 등
    stderr.txt         docker/claude stderr

규칙 (.claude/rules/harness.md, CLAUDE.md):
- 컨테이너에는 tasks/<id> 만 :ro 로 마운트한다. 프로젝트 루트·truth/·~/.claude 는 넣지 않는다
- 네트워크는 agentnet(--internal) + egress 프록시. 먼저 scripts/env_up.sh 실행
- 구독 한도 오류는 status=rate_limited 로 따로 기록한다 (점수에서 제외)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DISTRO = "Ubuntu-26.04"
IMAGE = "analyzer"
PROXY = "http://egress:8888"


# 이식성: 리눅스 도구(docker, nm, objdump)를 부르는 곳은 아래 두 함수뿐이다.
# 리눅스(WSL)에서는 직접 실행하고, Windows 에서는 wsl.exe 를 거친다 (docs/decisions.md 2026-11-11)
ON_WINDOWS = os.name == "nt"


def linux_path(p: Path) -> str:
    """리눅스 쪽에서 본 경로. Windows 면 C:\\Users\\... -> /mnt/c/Users/..."""
    p = p.resolve()
    if not ON_WINDOWS:
        return str(p)
    drive = p.drive.rstrip(":").lower()
    rest = p.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{rest}"


def linux(*args: str, **kw) -> subprocess.CompletedProcess:
    # Windows: --exec 로 로그인 셸(zsh)을 거치지 않고 인자를 그대로 넘긴다
    cmd = ["wsl.exe", "-d", DISTRO, "--exec", *args] if ON_WINDOWS else list(args)
    return subprocess.run(cmd, encoding="utf-8", errors="replace", **kw)


def load_condition(name: str) -> dict:
    cond = json.loads((ROOT / "conditions" / f"{name}.json").read_text(encoding="utf-8"))
    cond["prompt"] = (ROOT / "conditions" / cond["prompt_file"]).read_text(encoding="utf-8")
    return cond


def summarize_transcript(lines: list[str]) -> dict:
    tools: Counter[str] = Counter()
    tool_errors = 0  # 거부·실패·스키마 불일치 등 is_error 인 도구 결과. 많으면 status=ok 라도 분석이 막혔을 수 있다
    result = None
    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (ev.get("message") or {}).get("content")
        if ev.get("type") == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tools[block.get("name", "?")] += 1
        elif ev.get("type") == "user" and isinstance(content, list):
            tool_errors += sum(1 for b in content
                               if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"))
        elif ev.get("type") == "result":
            result = ev
    return {"tools": tools, "tool_errors": tool_errors, "result": result}


def classify(result: dict | None, timed_out: bool) -> str:
    if timed_out:
        return "timeout"
    if result is None:
        return "error"
    text = json.dumps(result, ensure_ascii=False).lower()
    if result.get("api_error_status") == 429 or "rate limit" in text or "usage limit" in text:
        return "rate_limited"
    if result.get("is_error"):
        return "error"
    if result.get("structured_output") is None:
        return "no_answer"
    return "ok"


def run_once(task_id: str, cond: dict, run_id: str) -> dict:
    task_dir = ROOT / "tasks" / task_id
    out_dir = ROOT / "runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=False)
    schema = (ROOT / "schema" / "answer.schema.json").read_text(encoding="utf-8")
    schema = json.dumps(json.loads(schema), separators=(",", ":"))

    # 권한 확인은 끈다: -p 에는 승인할 사람이 없어 r2 등이 자동 거부된다. 격리는 컨테이너가 담당
    # (읽기 전용 /work, agentnet + egress, 비root 사용자). 모든 조건에 공통인 실행 환경이므로 조건 파일이 아닌 여기 둔다
    claude_cmd = ('claude -p --output-format stream-json --verbose --permission-mode bypassPermissions '
                  '--model "$MODEL" --json-schema "$ANSWER_SCHEMA" '
                  '--disallowedTools "$DISALLOWED" ' + " ".join(cond["extra_args"]))
    docker = [
        "docker", "run", "--rm", "-i", "--name", run_id,
        "--network", "agentnet",
        "-e", f"HTTPS_PROXY={PROXY}", "-e", f"HTTP_PROXY={PROXY}",
        "-e", "CLAUDE_CODE_OAUTH_TOKEN",
        "-e", f"MODEL={cond['model']}",
        "-e", f"ANSWER_SCHEMA={schema}",
        "-e", f"DISALLOWED={','.join(cond['disallowed_tools'])}",
        "-v", f"{linux_path(task_dir)}:/work:ro",
        IMAGE, "bash", "-c", claude_cmd,
    ]

    env = dict(os.environ)
    if not env.get("CLAUDE_CODE_OAUTH_TOKEN"):
        sys.exit("CLAUDE_CODE_OAUTH_TOKEN 이 없습니다 (셸 환경 변수 확인)")
    if ON_WINDOWS:
        env["WSLENV"] = ":".join(filter(None, [env.get("WSLENV", ""), "CLAUDE_CODE_OAUTH_TOKEN/u"]))

    started = dt.datetime.now().astimezone()
    t0 = time.monotonic()
    timed_out = False
    try:
        proc = linux(*docker, input=cond["prompt"], capture_output=True,
                   timeout=cond["timeout_sec"], env=env)
        stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        rc = None
        linux("docker", "rm", "-f", run_id, capture_output=True)  # 클라이언트만 죽으면 컨테이너가 남는다
    elapsed = time.monotonic() - t0

    (out_dir / "transcript.jsonl").write_text(stdout, encoding="utf-8")
    (out_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    s = summarize_transcript(stdout.splitlines())
    result = s["result"] or {}
    status = classify(s["result"], timed_out)
    if result.get("structured_output") is not None:
        (out_dir / "answer.json").write_text(
            json.dumps(result["structured_output"], ensure_ascii=False, indent=2), encoding="utf-8")

    target = task_dir / "target"
    meta = {
        "run_id": run_id,
        "task": task_id,
        "condition": cond["name"],
        "model": cond["model"],
        "status": status,
        "exit_code": rc,
        "started": started.isoformat(timespec="seconds"),
        "wall_sec": round(elapsed, 1),
        "duration_ms": result.get("duration_ms"),
        "num_turns": result.get("num_turns"),
        "tool_calls": sum(s["tools"].values()),
        "tool_calls_by_name": dict(s["tools"]),
        "tool_errors": s["tool_errors"],
        "usage": result.get("usage"),
        "total_cost_usd": result.get("total_cost_usd"),
        "target_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "prompt_sha256": hashlib.sha256(cond["prompt"].encode()).hexdigest(),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id")
    ap.add_argument("--condition", default="baseline")
    ap.add_argument("--k", type=int, default=1, help="같은 과제 반복 횟수 (pass^k)")
    a = ap.parse_args()

    if not (ROOT / "tasks" / a.task_id / "target").exists():
        sys.exit(f"tasks/{a.task_id}/target 이 없습니다 (scripts/rebuild.sh 먼저)")
    cond = load_condition(a.condition)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    for i in range(1, a.k + 1):
        run_id = f"{stamp}_{a.task_id}_{cond['name']}_{i}"
        print(f"[{i}/{a.k}] {run_id} ...", flush=True)
        m = run_once(a.task_id, cond, run_id)
        print(f"    {m['status']}  {m['wall_sec']}s  turns={m['num_turns']}  tools={m['tool_calls']}", flush=True)


if __name__ == "__main__":
    main()
