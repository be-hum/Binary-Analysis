---
paths:
  - "docker/**"
---

# 마운트 규칙

- truth/ 는 analyzer 컨테이너에 어떤 형태로도 마운트하지 않는다 (상위 디렉터리 마운트로 딸려 들어가는 것도 금지)
- TODO: analyzer가 볼 수 있는 경로 목록(바이너리, conditions/ 등)과 읽기 전용 여부
