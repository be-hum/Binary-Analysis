---
paths:
  - "harness/**"
---

# 채점·기록 규칙

- 평가 대상 에이전트는 analyzer 컨테이너 안에서 `claude -p`(구독 OAuth 토큰)로 실행한다. `--bare`는 OAuth를 못 읽으므로 쓰지 않는다
- 실행마다 runs/<run_id>/ 에 transcript, 답안, 점수, 토큰, 도구 호출 수, 시간을 남긴다
- 코드로 채점할 수 있는 항목은 LLM judge에 맡기지 않는다
- 한 실험에서 바꾸는 변수는 하나. 조건은 conditions/ 의 파일로만 지정한다
- TODO: 이해 점수 계산식, pass^3 판정 방식
