# 현재 상태

- 단계: M0 (환경·정답지) — 환경 구축 순서는 docs/plan.md 6장
- 완료: 1 `.wslconfig`(16GB/6코어/swap 8GB) · 2 git init·디렉터리 뼈대 · 4 Windows→WSL Docker 호출, 공백 경로 :ro 마운트 확인 · 3 OAuth 토큰(108자) 사용자 환경 변수 + WSLENV, Windows `claude -p`·WSL 전달 확인 (2026-11-10) · 5 arvo subset 6과제 -vul/-fix 이미지, 10400 데이터 · 6 10400 재빌드(`scripts/rebuild.sh 10400 mng_get_long`): 대상 0x4b7880, gdb 호출 스택이 크래시 스택과 줄 번호까지 일치 · 7·8 `scripts/env_up.sh`: analyzer(Ghidra 12.1, JDK 21, r2 6.2.6, Claude Code 2.1.322) + agentnet(--internal) + egress(tinyproxy, api.anthropic.com만) · 9 `scripts/smoke_test.sh` 14/14 PASS, 컨테이너 안 Ghidra 자동 분석 2분 13초 · 10 `harness/run_task.py` + `conditions/baseline`: 10400 1회 ok (282초, 도구 17회, 경로 F1 0.678) · `harness/grade.py`: 경로 코드 채점 + Opus judge 동작 확인
- 다음 할 일:
  - 방향 전환(2026-11-11): 진단 중심 채점. 스키마 `calls_next_at`/`evidence`, 호출 지점 코드 검증, failure_type, gate_ok, human.json 양식 구현
  - 10400 정답지: Claude 초안(예외) → 사용자 확인 (main·LLVMFuzzerTestOneInput 포인트는 coder_fuzzer.cc로 확인 필요)
  - baseline 10400 새 스키마 1회 완료 (`runs/20261111-154853_10400_baseline_1`): total 0.757, 경로 1.0, input 0 (pHYs 경로 선택 — 정답지는 LOOP) → 과제에 호출 지점 0x4b1456 추가, 재실행 필요. human.json 직접 채점 → judge 비교
  - 368·1065 재빌드(`scripts/rebuild/<id>.sh`), 정답지 2개
  - judge 보정: 3과제 직접 채점과 비교
- 막힌 것: 없음
