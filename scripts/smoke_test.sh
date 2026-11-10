#!/bin/bash
# usage (WSL): scripts/smoke_test.sh [task id, 기본 10400]
# analyzer 컨테이너가 평가 실행 조건을 만족하는지 확인한다 (plan.md 6장 9단계).
# 먼저 scripts/env_up.sh 로 이미지·네트워크를 준비해야 한다.
set -uo pipefail
ID="${1:-10400}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$HERE")"
TASK="$PROJ/tasks/$ID"
RUN=(docker run --rm --network agentnet -e HTTPS_PROXY=http://egress:8888 -e HTTP_PROXY=http://egress:8888
     -e CLAUDE_CODE_OAUTH_TOKEN -v "$TASK:/work:ro" analyzer)
pass=0; fail=0
check() {  # check "<설명>" <기대: ok|fail> <명령...>
  local desc="$1" want="$2"; shift 2
  local out; out=$("$@" 2>&1); local rc=$?
  local got=ok; [ $rc -ne 0 ] && got=fail
  if [ "$got" = "$want" ]; then echo "PASS  $desc"; pass=$((pass+1)); else echo "FAIL  $desc (rc=$rc)"; fail=$((fail+1)); fi
  echo "$out" | head -3 | sed 's/^/        /'
}

echo "== 1. 도구 =="
check "java 21"             ok "${RUN[@]}" java -version
check "Ghidra headless"     ok "${RUN[@]}" bash -c 'grep application.version /opt/ghidra/Ghidra/application.properties && test -x /opt/ghidra/support/analyzeHeadless'
check "radare2"             ok "${RUN[@]}" r2 -v
check "binutils objdump"    ok "${RUN[@]}" objdump --version
check "Claude Code"         ok "${RUN[@]}" claude --version

echo "== 2. 마운트 격리 =="
check "/work 는 target, task.md 만" ok "${RUN[@]}" bash -c 'ls /work; [ "$(ls /work | tr "\n" " ")" = "target task.md " ]'
check "/work 쓰기 불가"      fail "${RUN[@]}" touch /work/x
check "truth/ 없음"          fail "${RUN[@]}" bash -c 'find / -xdev \( -name truth -o -name target.debug -o -name poc -o -name CLAUDE.md \) 2>/dev/null | grep -q .'
check "~/.claude 비어 있음"  fail "${RUN[@]}" bash -c 'ls -A ~/.claude ~/.claude.json 2>/dev/null | grep -q .'

echo "== 3. 네트워크 격리 =="
check "프록시 경유 example.com 차단"  fail "${RUN[@]}" curl -sS -m 10 -o /dev/null https://example.com
check "프록시 우회 직접 접속 차단"    fail "${RUN[@]}" curl -sS -m 10 --noproxy '*' -o /dev/null https://example.com
check "프록시 경유 api.anthropic.com 허용" ok "${RUN[@]}" bash -c 'code=$(curl -sS -m 15 -o /dev/null -w "%{http_code}" https://api.anthropic.com/v1/messages); echo "http $code"; [ "$code" != 000 ]'

echo "== 4. claude -p =="
check "claude -p 응답 (구독 토큰, 프록시 경유)" ok "${RUN[@]}" bash -c 'claude -p "reply with only: ok" --max-turns 1 --disallowedTools WebSearch,WebFetch | grep -qi ok && echo ok'
check "개발용 CLAUDE.md 내용을 모름" ok "${RUN[@]}" bash -c 'a=$(claude -p "이 환경에 프로젝트 지침(CLAUDE.md)이나 진행 단계(M0, M1 등) 정보가 주어져 있나? 있으면 그 단계 이름을, 없으면 NONE 한 단어만 답해." --max-turns 1 --disallowedTools WebSearch,WebFetch); echo "$a"; echo "$a" | grep -q NONE'

echo "== 결과: PASS $pass / FAIL $fail =="
[ $fail -eq 0 ]
