# 현재 상태

- 단계: M0 (환경·정답지) — 환경 구축 순서는 docs/plan.md 6장
- 완료: 1 `.wslconfig`(16GB/6코어/swap 8GB) · 2 git init·디렉터리 뼈대 · 4 Windows→WSL Docker 호출, 공백 경로 :ro 마운트 확인 · 3 OAuth 토큰(108자) 사용자 환경 변수 + WSLENV, Windows `claude -p`·WSL 전달 확인 (2026-11-10) · 5 arvo subset 6과제 -vul/-fix 이미지, 10400 데이터 · 6 10400 재빌드(`scripts/rebuild.sh 10400 mng_get_long`): 대상 0x4b7880, gdb 호출 스택이 크래시 스택과 줄 번호까지 일치 · 7·8 `scripts/env_up.sh`: analyzer(Ghidra 12.1, JDK 21, r2 6.2.6, Claude Code 2.1.322) + agentnet(--internal) + egress(tinyproxy, api.anthropic.com만) · 9 `scripts/smoke_test.sh` 14/14 PASS, 컨테이너 안 Ghidra 자동 분석 2분 13초
- 다음 할 일:
  - 10 하네스 뼈대 `harness/run_task.py` → arvo:10400 1회 실행
  - 정답지 3개(10400, 368, 1065), `grade.py`
- 막힌 것: 없음
