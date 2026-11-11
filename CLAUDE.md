# Binary Analysis Agent

## 목표
strip된 C 바이너리와 대상 함수 주소를 받아 프로그램 목적, 입력 경로,
경로상 함수 역할, 대상 함수에 닿는 입력 부분을 설명하는 에이전트.
답이 알려진 과제로 채점(코드 + 사람 + LLM judge)해 실패 유형을 진단하고, 그 결과로 에이전트 설계 방향을 잡는다.
단계 기준(잠정): gate_ok(점수 0.9 이상 + 틀린 주장·잘못된 호출 지점 0건)를 pass^3.

## 현재 상태
@docs/status.md

## 단계 (상세: docs/plan.md 5장)
M0 환경·정답지 → M1 무지침 기준선 → M2 Ghidra 도구 4개
→ M3 변수 실험(구조 변수 / 프롬프트 변수 분리) → M4 1-day 점검

## 절대 규칙
- truth/ 는 analyzer 컨테이너에 절대 마운트하지 않는다
- 평가 대상 에이전트는 analyzer 컨테이너 안에서 `claude -p`(구독 OAuth 토큰)로 실행한다. 컨테이너에는 프로젝트 루트·`~/.claude`를 넣지 않는다 (이 CLAUDE.md가 새지 않게)
- 실험은 한 번에 변수 하나만 바꾼다. 조건 파일은 conditions/ 에 둔다
- 모든 실행은 runs/<run_id>/ 에 transcript, 답안, 점수, 토큰, 도구 호출 수, 시간을 남긴다
- 코드로 채점할 수 있는 항목은 LLM judge에 맡기지 않는다

## 참고 문서 (필요할 때 읽기)
- 전체 계획과 과제 목록: docs/plan.md
- 지금까지의 결정과 이유: docs/decisions.md
