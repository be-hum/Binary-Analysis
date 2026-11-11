---
paths:
  - "truth/**"
---

# 정답지 작성 규칙

정답지는 사용자가 직접 쓰고 Claude는 검토만 한다 (소스·gdb로 사실 확인, 누락 지적). Claude가 포인트를 대신 채우지 않는다.

## truth/<id>/truth.json 형식
- 함수는 **심볼 이름**으로 적는다. 채점기가 답안 주소를 target.debug 심볼로 바꿔 비교한다 (C++은 `nm -C` 표기)
- `path.required`: main부터 대상까지 호출 순서대로. 출처는 `-g` 빌드의 gdb 호출 스택
- `path.allowed`: 경로에 끼어도 감점하지 않는 함수 (예: 실제로 거치는 헬퍼)
- `purpose.points` / `functions.<심볼>.points` / `input.points`: 답안에 반드시 들어가야 할 사실 2~4개.
  한 포인트는 judge가 충족/미충족을 판정할 수 있는 한 문장. 소스로 확인된 사실만 쓴다
  - `functions` 포인트는 답안의 role + consumes 를 함께 본다
  - `input` 포인트는 답안의 input_format + target.input_reaching 을 함께 본다 (필드, 크기, 위치)

## 채점 (harness/grade.py)
- 경로 0.4 (코드): recall = 순서를 지킨 필수 노드(LCS) / 필수 노드 수, precision = 필수+허용 노드 / 답안 노드 수, 점수 = F1
- 함수 역할 0.3 / 입력 부분 0.2 / 목적 0.1 (judge): 충족 포인트 비율. 포인트와 모순되는 내용은 1개당 1포인트 감점(최저 0).
  confidence `unknown` 은 감점 없이 0점
- 호출 지점 (코드): 답안 `calls_next_at`을 target.debug에서 디스어셈블해 verified / indirect / wrong_callee / not_call / outside_function / missing
- 진단: judge·사람 공통 failure_type(omission / vague / wrong_claim / misattributed) + 코드 태그 → score.json `diagnosis`. 사람 채점은 runs/<id>/human.json
- 호출 지점: 과제가 지정한 `target.call_site`와 답안 마지막 단계가 다르면 `call_site_other_call_site`
