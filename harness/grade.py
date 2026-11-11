"""runs/<run_id>/answer.json 을 truth/<task>/truth.json 으로 채점해 runs/<run_id>/score.json 에 쓴다.

usage (WSL/리눅스, 프로젝트 루트에서. Windows 에서도 동작):
    python harness/grade.py runs/<run_id> [--no-judge]
    python harness/grade.py runs/*_10400_*            # 여러 개

채점 규칙 (.claude/rules/truth.md):
- 경로 0.4 (코드): 답안 주소 → target.debug 심볼(주소가 함수 안쪽이어도 그 함수로).
  recall = LCS(답안, 필수) / 필수 수, precision = (필수+허용 안의 노드) / 답안 노드 수, F1.
  _start 는 모든 과제 공통 허용 노드
- 함수 역할 0.3 / 입력 부분 0.2 / 목적 0.1 (Opus judge): 포인트별 met / not_met / contradicted.
  항목 점수 = max(0, met - contradicted) / 포인트 수. confidence unknown 이거나 답이 없으면 judge 없이 0
- judge 는 컨테이너 밖(호스트)에서 claude -p, 도구 없음, 프로젝트 밖 임시 디렉터리에서 실행 (CLAUDE.md 차단)
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_task import ON_WINDOWS, ROOT, linux, linux_path  # noqa: E402

WEIGHTS = {"path": 0.4, "functions": 0.3, "input": 0.2, "purpose": 0.1}
COMMON_ALLOWED = {"_start"}
JUDGE_MODEL = "claude-opus-5-5"
JUDGE_TIMEOUT = 600

# 진단 태그 (judge·사람 공통). 코드 태그는 path_missing / path_extra / call_site_* / declared_unknown
FAILURE_TYPES = ["none", "omission", "vague", "wrong_claim", "misattributed"]
# 잠정 단계 기준 (docs/decisions.md 2026-11-11): 같은 조건 3회 모두 gate_ok
GATE_TOTAL = 0.9

JUDGE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "verdicts"],
                "properties": {
                    "id": {"type": "string"},
                    "verdicts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["point", "verdict", "failure_type", "reason"],
                            "properties": {
                                "point": {"type": "integer"},
                                "verdict": {"type": "string", "enum": ["met", "not_met", "contradicted"]},
                                "failure_type": {"type": "string", "enum": FAILURE_TYPES},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }
    },
}

JUDGE_PROMPT = """You are grading answers produced by a reverse-engineering agent that analyzed a stripped binary.
For each item below you get a list of reference points (facts verified from source code) and the agent's answer text for that item.

For every point, decide:
- "met": the answer states this fact. Paraphrase is fine, and so is a hedged statement ("probably X") when X is correct. Exact function or symbol names are required only when the point itself asks for a name.
- "contradicted": the answer asserts something incompatible with this point (a wrong claim, not just a missing one).
- "not_met": the answer neither states nor contradicts it.

Also set "failure_type":
- "none" when met.
- "omission": the fact is simply absent.
- "vague": the answer gestures at it but too generally to count (e.g. "reads some fields").
- "wrong_claim": the answer asserts something false about it (use with "contradicted").
- "misattributed": the fact appears but is assigned to the wrong function, field, or offset.

Judge only the given answer text for that item. Do not use other items or outside knowledge to fill gaps in the answer.
Give a one-sentence reason for each verdict. Return a verdict for every point, indexed from 0, for every item.

ITEMS:
{items}
"""


# ---------- 심볼 ----------

def load_symbols(task_id: str) -> list[tuple[int, int, str]]:
    """(start, size, demangled name) 목록. truth/<id>/symbols.tsv 에 캐시 (nm -C 가 필요해 WSL 사용)"""
    tdir = ROOT / "truth" / task_id
    cache = tdir / "symbols.tsv"
    debug = tdir / "target.debug"
    if not cache.exists() or cache.stat().st_mtime < debug.stat().st_mtime:
        p = linux("nm", "-C", "-S", "--defined-only", linux_path(debug), capture_output=True, check=True)
        rows = []
        for line in p.stdout.splitlines():
            parts = line.split(" ", 3)
            if len(parts) == 4 and parts[2] in "tTwW":
                rows.append(f"{parts[0]}\t{parts[1]}\t{parts[3]}")
        cache.write_text("\n".join(rows) + "\n", encoding="utf-8")
    syms = []
    for line in cache.read_text(encoding="utf-8").splitlines():
        a, s, n = line.split("\t", 2)
        syms.append((int(a, 16), int(s, 16), n))
    return syms


def resolver(syms: list[tuple[int, int, str]]):
    def resolve(addr: str) -> str:
        try:
            x = int(addr, 16)
        except ValueError:
            return f"?{addr}"
        for start, size, name in syms:
            if start == x or start <= x < start + size:
                return name
        return f"?{addr}"
    return resolve


# ---------- 경로 ----------

def lcs_len(a: list[str], b: list[str]) -> int:
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            dp[i + 1][j + 1] = dp[i][j] + 1 if x == y else max(dp[i][j + 1], dp[i + 1][j])
    return dp[-1][-1]


def score_path(answer_path: list[str], truth_path: dict) -> dict:
    seq = []
    for n in answer_path:  # 연속 중복 제거 (placeholder 반복 등)
        if not seq or seq[-1] != n:
            seq.append(n)
    required = truth_path["required"]
    ok_nodes = set(required) | set(truth_path.get("allowed", [])) | COMMON_ALLOWED
    recall = lcs_len(seq, required) / len(required) if required else 0.0
    precision = sum(1 for n in seq if n in ok_nodes) / len(seq) if seq else 0.0
    f1 = 2 * recall * precision / (recall + precision) if recall + precision else 0.0
    return {
        "score": round(f1, 4), "recall": round(recall, 4), "precision": round(precision, 4),
        "answer_symbols": seq,
        "missing": [n for n in required if n not in seq],
        "extra": [n for n in seq if n not in ok_nodes],
    }


# ---------- judge ----------

def claude_exe() -> str:
    if os.environ.get("CLAUDE_EXE"):
        return os.environ["CLAUDE_EXE"]
    w = shutil.which("claude")
    if w and not ON_WINDOWS:
        return w
    if w:
        # npm 래퍼(.cmd)는 cmd.exe 를 거쳐 JSON 인자의 따옴표를 깨뜨린다 → 실제 exe 를 직접 부른다
        exe = Path(w).parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
        if exe.exists():
            return str(exe)
        return w
    sys.exit("claude 실행 파일을 찾지 못했습니다 (CLAUDE_EXE 로 지정)")


def run_judge(items: list[dict]) -> dict:
    payload = json.dumps([{"id": i["id"], "points": i["points"], "answer": i["answer"]} for i in items],
                         ensure_ascii=False, indent=2)
    with tempfile.TemporaryDirectory(prefix="judge_") as tmp:  # 프로젝트 밖: CLAUDE.md·rules 가 섞이지 않게
        p = subprocess.run(
            # --system-prompt: Claude Code 기본 시스템 프롬프트(에이전트용, 큼)를 judge 용 한 줄로 교체해 비용을 줄인다
            [claude_exe(), "-p", "--model", JUDGE_MODEL, "--tools", "", "--output-format", "json",
             "--system-prompt", "You are a strict, careful grader. Follow the user's grading instructions exactly.",
             "--json-schema", json.dumps(JUDGE_SCHEMA, separators=(",", ":"))],
            input=JUDGE_PROMPT.format(items=payload), capture_output=True,
            encoding="utf-8", errors="replace", cwd=tmp, timeout=JUDGE_TIMEOUT)
    try:
        res = json.loads(p.stdout)
    except json.JSONDecodeError:
        sys.exit(f"judge 출력 파싱 실패 (rc={p.returncode}): {p.stdout[:500]} {p.stderr[:500]}")
    if res.get("is_error") or res.get("structured_output") is None:
        sys.exit(f"judge 실패: {json.dumps(res, ensure_ascii=False)[:800]}")
    return {"verdicts": {it["id"]: it["verdicts"] for it in res["structured_output"]["items"]},
            "usage": res.get("usage"), "total_cost_usd": res.get("total_cost_usd"),
            "duration_ms": res.get("duration_ms")}


def item_score(points: list[str], verdicts: list[dict]) -> float:
    v = {d["point"]: d["verdict"] for d in verdicts}
    if set(v) != set(range(len(points))):
        raise ValueError(f"judge 가 포인트 {len(points)}개 중 {sorted(v)} 만 판정함")
    met = sum(1 for x in v.values() if x == "met")
    bad = sum(1 for x in v.values() if x == "contradicted")
    return max(0, met - bad) / len(points)


# ---------- 호출 지점 (코드 검증) ----------

def disasm_at(task_id: str, addrs: list[int]) -> dict[int, str]:
    """target.debug 에서 각 주소의 명령 한 줄 (WSL objdump, 1회 호출)"""
    if not addrs:
        return {}
    dbg = linux_path(ROOT / "truth" / task_id / "target.debug")
    script = 'for a in "$@"; do echo "@@$a"; objdump -d --no-show-raw-insn -C '              '--start-address=$a --stop-address=$((a+16)) "$0" | grep -E "^ +[0-9a-f]+:" | head -1; done'
    p = linux("bash", "-c", script, dbg, *[hex(a) for a in addrs], capture_output=True, check=True)
    out, cur = {}, None
    for line in p.stdout.splitlines():
        if line.startswith("@@"):
            cur = int(line[2:], 16); out[cur] = ""
        elif cur is not None and not out[cur]:
            out[cur] = line.split(":", 1)[1].strip()
    return out


def check_call_sites(task_id: str, ans: dict, resolve) -> list[dict]:
    """각 경로 함수의 calls_next_at 이 (그 함수 안의) 다음 함수로 가는 call/jmp 인지"""
    path = ans["entry_path"]
    funcs = {f["addr"].lower(): f for f in ans.get("functions", [])}
    todo = []
    for i, a in enumerate(path[:-1]):
        f = funcs.get(a.lower())
        site = f.get("calls_next_at") if f else None
        todo.append((a, path[i + 1], site))
    ins = disasm_at(task_id, [int(s, 16) for _, _, s in todo if s])
    res = []
    for a, nxt, site in todo:
        r = {"from": resolve(a), "to": resolve(nxt), "site": site}
        if not site:
            r["result"] = "missing"
        else:
            x = int(site, 16); text = ins.get(x, ""); r["insn"] = text
            op = text.split()[0] if text else ""
            if resolve(a) == "_start":
                r["result"] = "indirect"  # main 은 __libc_start_main 인자로 넘어간다
            elif resolve(site) != resolve(a):
                r["result"] = "outside_function"
            elif not (op.startswith("call") or op.startswith("jmp")):
                r["result"] = "not_call"
            elif "*" in text:
                r["result"] = "indirect"  # 함수 포인터·가상 호출: 대상은 코드로 확인 불가
            else:
                tgt = text.split()[1] if len(text.split()) > 1 else ""
                r["result"] = "verified" if tgt and resolve(tgt) == resolve(nxt) else "wrong_callee"
        res.append(r)
    return res


def diagnose(path: dict, call_sites: list[dict], per_item: dict) -> list[dict]:
    d = [{"item": "path", "type": "path_missing", "detail": n} for n in path["missing"]]
    d += [{"item": "path", "type": "path_extra", "detail": n} for n in path["extra"]]
    d += [{"item": f"call:{c['from']}->{c['to']}", "type": f"call_site_{c['result']}", "detail": c.get("insn", "")}
          for c in call_sites if c["result"] not in ("verified", "indirect")]
    for iid, it in per_item.items():
        if "reason" in it:
            d.append({"item": iid, "type": "declared_unknown" if "unknown" in it["reason"] else "omission",
                      "detail": it["reason"]})
        for v in it.get("verdicts", []):
            if v["verdict"] != "met":
                d.append({"item": iid, "type": v.get("failure_type", "?"), "point": v["point"], "detail": v["reason"]})
    return d


def write_human_template(run_dir: Path, truth: dict) -> None:
    """사람 채점용 빈 양식 (judge 와 같은 태그) — 이미 있으면 건드리지 않는다"""
    f = run_dir / "human.json"
    if f.exists():
        return
    items = {f"function:{s}": sp["points"] for s, sp in truth["functions"].items()}
    items["input"] = truth["input"]["points"]; items["purpose"] = truth["purpose"]["points"]
    tpl = {"_how": f"verdict: met|not_met|contradicted, failure_type: {'|'.join(FAILURE_TYPES)}",
           "items": {k: [{"point": i, "text": t, "verdict": "", "failure_type": "", "note": ""}
                         for i, t in enumerate(v)] for k, v in items.items()}}
    f.write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- 채점 ----------

def has_todo(points: list[str]) -> bool:
    return not points or any(p.strip().upper().startswith("TODO") for p in points)


def grade(run_dir: Path, use_judge: bool) -> dict:
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    task_id = meta["task"]
    truth = json.loads((ROOT / "truth" / task_id / "truth.json").read_text(encoding="utf-8"))
    ans_file = run_dir / "answer.json"
    if meta["status"] != "ok" or not ans_file.exists():
        # rate_limited 는 점수에서 제외, 나머지(timeout/error/no_answer)는 0점
        return {"run_id": meta["run_id"], "task": task_id, "status": meta["status"],
                "total": None if meta["status"] == "rate_limited" else 0.0}
    ans = json.loads(ans_file.read_text(encoding="utf-8"))
    resolve = resolver(load_symbols(task_id))

    path = score_path([resolve(a) for a in ans["entry_path"]], truth["path"])

    # 답안 함수(경로 함수 + 대상)를 심볼별로 모은다
    by_sym: dict[str, dict] = {}
    for f in ans.get("functions", []):
        by_sym.setdefault(resolve(f["addr"]), {"text": f"role: {f['role']}\nconsumes: {f['consumes']}",
                                               "confidence": f["confidence"]})
    t = ans["target"]
    by_sym[resolve(t["addr"])] = {"text": f"role: {t['role']}", "confidence": t["confidence"]}

    items, fixed = [], {}  # fixed: judge 없이 0점이 정해진 항목
    for sym, spec in truth["functions"].items():
        iid = f"function:{sym}"
        a = by_sym.get(sym)
        if a is None or a["confidence"] == "unknown":
            fixed[iid] = {"score": 0.0, "reason": "no answer" if a is None else "confidence unknown"}
        else:
            items.append({"id": iid, "points": spec["points"], "answer": a["text"]})
    items.append({"id": "input", "points": truth["input"]["points"],
                  "answer": f"input_format: {ans['input_format']}\n"
                            f"input_reaching_target: {t['input_reaching']}"
                            + ("\n(confidence: unknown)" if t["confidence"] == "unknown" else "")})
    items.append({"id": "purpose", "points": truth["purpose"]["points"], "answer": ans["program_purpose"]})

    todo = [i["id"] for i in items if has_todo(i["points"])] + \
           [f"function:{s}" for s, sp in truth["functions"].items() if has_todo(sp["points"]) and f"function:{s}" in fixed]
    call_sites = check_call_sites(task_id, ans, resolve)
    want = truth["target"].get("call_site")
    if want and call_sites:
        last = call_sites[-1]
        last["expected_site"] = want
        if not last["site"] or int(last["site"], 16) != int(want, 16):
            last["result"] = "other_call_site"  # 대상에 닿긴 해도 과제가 지정한 호출이 아님
    write_human_template(run_dir, truth)
    result = {"run_id": meta["run_id"], "task": task_id, "status": "ok", "path": path, "call_sites": call_sites}
    if not use_judge or todo:
        result.update({"total": None, "judge": None,
                       "note": "judge 생략" if not use_judge else f"정답지 TODO 미작성: {sorted(set(todo))}"})
        return result

    j = run_judge(items)
    per_item = dict(fixed)
    for it in items:
        per_item[it["id"]] = {"score": round(item_score(it["points"], j["verdicts"][it["id"]]), 4),
                              "verdicts": j["verdicts"][it["id"]]}
    fn_ids = [f"function:{s}" for s in truth["functions"]]
    functions = sum(per_item[i]["score"] for i in fn_ids) / len(fn_ids)
    parts = {"path": path["score"], "functions": round(functions, 4),
             "input": per_item["input"]["score"], "purpose": per_item["purpose"]["score"]}
    result.update({
        "parts": parts,
        "total": round(sum(WEIGHTS[k] * v for k, v in parts.items()), 4),
        "diagnosis": diagnose(path, call_sites, per_item),
        "items": per_item,
        "judge": {"model": JUDGE_MODEL, "usage": j["usage"], "total_cost_usd": j["total_cost_usd"],
                  "duration_ms": j["duration_ms"]},
    })
    bad = [x for x in result["diagnosis"] if x["type"] in ("wrong_claim", "misattributed")
           or x["type"].startswith("call_site_") and x["type"] != "call_site_missing"]
    result["gate_ok"] = result["total"] >= GATE_TOTAL and not bad
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="runs/<run_id> (glob 가능)")
    ap.add_argument("--no-judge", action="store_true", help="경로(코드 채점)만")
    a = ap.parse_args()
    dirs = [Path(p) for pat in a.runs for p in (glob.glob(pat) or [pat])]
    for d in dirs:
        r = grade(d, not a.no_judge)
        (d / "score.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        p = r.get("path") or {}
        print(f"{d.name}: status={r['status']} total={r['total']} "
              f"path={p.get('score')} (R={p.get('recall')} P={p.get('precision')}) "
              f"parts={r.get('parts')} gate_ok={r.get('gate_ok')} {r.get('note', '')}")
        for x in r.get("diagnosis", []):
            print(f"    [{x['type']}] {x['item']}: {x['detail'][:100]}")


if __name__ == "__main__":
    main()
