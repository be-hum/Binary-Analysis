# 결정 기록

| 날짜 | 결정 | 이유 |
|---|---|---|
| 2026-11-09 | 평가 대상 에이전트는 analyzer 컨테이너 안에서 `claude -p`로 실행 (처음엔 `--bare`였으나 같은 날 변경) | 구독을 쓰려면 OAuth가 필요한데 `--bare`는 OAuth를 읽지 않음. CLAUDE.md·rules 유출은 컨테이너에 프로젝트 루트와 `~/.claude`를 넣지 않는 것으로 막음 |
| 2026-11-09 | truth/ 는 analyzer 컨테이너에 마운트하지 않음 | 에이전트가 정답지를 볼 수 없게 |
| 2026-11-09 | 개발·하네스는 Windows, Docker·큰 데이터는 WSL(docker-ce), 에이전트는 컨테이너 안에서만 | 마운트하는 데이터가 작아 `/mnt/c` 성능 손해가 미미하고, PyCharm·Ghidra GUI·Windows Ollama 연동이 Windows 쪽이 편함. Docker Desktop은 쓰지 않음 |
| 2026-11-09 | analyzer 인증은 구독 OAuth 토큰 (`claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN`) | API 종량제 대신 구독 사용. 사용량은 구독 한도에 포함됨 |
| 2026-11-10 | 비계측 재빌드는 `-O2 -fno-inline -g` 한 번 빌드 → strip 복사본을 과제용으로 | 대상 함수가 작은 static 함수면 -O2에서 인라인돼 주소가 사라짐(10400 `mng_get_long`). 소스 패치 없이 함수 경계를 소스와 1:1로 유지. 한 빌드에서 둘을 만들어 주소가 반드시 일치 |
| 2026-11-10 | 하네스는 원본 fuzz target + libFuzzer `StandaloneFuzzTargetMain.c` | 경로가 크래시 스택과 같아 정답지 출처가 명확하고 PoC 단계와 이어짐. 10400은 맨 위 두 단계(LLVMFuzzerTestOneInput, Magick::Image::read)만 C++ |
| 2026-11-10 | 과제 바이너리 이름은 `target`으로 통일, PoC는 truth/에만 | fuzzer 이름(`coder_MNG_fuzzer`)과 PoC가 입력 형식 힌트가 되지 않게 |
| 2026-11-10 | 웹 차단은 `--internal` 네트워크 + tinyproxy 허용 목록(`^api\.anthropic\.com$`, CONNECT 443만) | CyberGym proxy 대신 구성이 단순하고, 직접 접속은 DNS부터 안 되며 프록시 경유도 허용 호스트만 통과. Claude Code는 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`로 다른 호스트를 부르지 않음 |
| 2026-11-10 | radare2는 apt(5.5.0) 대신 GitHub 릴리스 deb(6.2.6), Ghidra는 공식 zip을 sha256 확인 후 설치 | apt 판이 너무 오래됨. Ghidra는 Windows GUI와 같은 12.1로 맞춤 |
| 2026-11-10 | 재빌드 바이너리·PoC·과제 원자료는 git 제외 | `scripts/rebuild.sh`로 재생성, `build_info.txt`의 sha256으로 동일성 확인 |
| 2026-11-10 | 정답지는 사용자가 쓰고 Claude가 검토 | 정답지 작성이 리버싱 연습 (plan.md 3장) |
| 2026-11-10 | 정답 경로는 main부터, 필수 + 허용 목록, 순서 반영 F1 | main까지가 strip 바이너리에서 찾을 수 있는 실제 시작점. 합리적인 헬퍼를 끼워 넣은 답을 감점하지 않으려고 허용 목록을 둠 |
| 2026-11-10 | judge 항목은 핵심 포인트 체크리스트, unknown 0점·모순 1포인트 감점 | 포인트별 충족 판정이 재현 가능하고 사람 채점과 맞추기 쉬움. 모르면 모른다고 하게 유도 (hallucination 억제) |
| 2026-11-10 | M1 기준선 조건: 과제 설명 + 도구 위치만, Sonnet 5.5 고정, 30분 상한, 턴 제한 없음 (`conditions/baseline.*`) | 도구를 몰라서 못 쓰는 문제는 피하되 분석 방법은 주지 않음. 실험 내내 모델 고정. 로컬 LLM으로 갈 것을 생각하면 최상위 모델보다 방법론 효과가 잘 드러남 |
| 2026-11-10 | judge는 Windows에서 `claude -p` Opus 5.5, 도구 없음, 프로젝트 밖 디렉터리에서 실행 | 정답지를 봐야 하므로 컨테이너 밖. 평가 대상보다 강한 모델로 판정. CLAUDE.md가 judge에 섞이지 않게 |
| 2026-11-10 | 정답지용 소스는 WSL `~/src/<id>`에 풀어 `\\wsl$`로 열람 | 저장소·컨테이너와 분리 |
| 2026-11-10 | 컨테이너 안 `claude -p`는 `--permission-mode bypassPermissions` (하네스 공통, 조건 파일 아님) | `-p`에는 승인자가 없어 r2 등 Bash가 자동 거부돼 분석이 불가능했음(실측). 격리는 컨테이너(읽기 전용 /work, agentnet, 비root)가 담당 |
| 2026-11-10 | `_start`는 모든 과제 공통 허용 경로 노드 | strip 바이너리에서 자연스러운 출발점. 감점도 가점도 없음 |
| 2026-11-10 | judge는 `--system-prompt`로 기본 시스템 프롬프트를 한 줄로 교체, npm 래퍼 대신 `claude.exe` 직접 호출 | 같은 판정에 비용 $1.46 → $0.019. `.cmd` 래퍼는 JSON 인자 따옴표를 깨뜨림 |
| 2026-11-10 | 주소→심볼은 WSL `nm -C -S` 결과를 `truth/<id>/symbols.tsv`에 캐시 | C++ 이름 demangle이 필요. 함수 안쪽 주소도 해당 함수로 매핑 |
| 2026-11-09 | 컨텍스트 구조: CLAUDE.md(항상) + docs/status.md(import) + .claude/rules/(경로별) | 항상 읽히는 분량을 줄이고, 규칙은 해당 파일을 다룰 때만 로드 |
| 2026-11-11 | 10400 정답지 포인트는 예외로 Claude가 초안 작성 (사용자 요청) | 사용자가 형식·수준을 익힐 예시가 필요. judge가 Claude 쪽으로 치우칠 수 있으므로 사용자 검토 후 확정, 이후 과제는 사용자 작성 원칙 유지 |
| 2026-11-11 | 평가 목적을 "점수 통과"에서 "실패 진단 → 설계 방향"으로 전환. 채점 결과에 diagnosis(실패 유형 태그) 추가 | 답이 알려진 프로그램에서 어디가 미흡한지 보고 에이전트 설계를 잡기 위함 |
| 2026-11-11 | 답안 경로의 각 단계에 `calls_next_at`(다음 함수로 넘기는 call/jmp 주소)과 `evidence` 요구, 호출 지점은 target.debug objdump로 코드 검증 | 경로를 근거와 함께 명시하게 해 환각을 줄이고, 검증 가능한 것은 judge 대신 코드로 |
| 2026-11-11 | judge 판정에 failure_type(omission/vague/wrong_claim/misattributed) 추가, 사람 채점은 같은 태그의 runs/<id>/human.json 으로 | judge와 사람 채점을 항목·태그 단위로 비교 |
| 2026-11-11 | 단계 기준(잠정): run마다 gate_ok = total ≥ 0.9 이고 wrong_claim·misattributed·잘못된 호출 지점 0건, 같은 조건 3회 모두 gate_ok면 통과 | 사용자가 판단 기준이 생길 때까지 고정. 점수가 높아도 틀린 주장이 있으면 통과시키지 않음 (환각 억제가 목표) |
| 2026-11-11 | 10400 input 포인트에서 버퍼 초과 읽기(버그 조건) 문장 제거 | 평가 대상은 취약점 탐지가 아니라 대상 함수까지의 입력 이해 |
| 2026-11-11 | 과제에 대상 함수 주소와 함께 "관심 호출 지점"(크래시 스택 #1 줄의 call 주소)을 준다. 정답지 `target.call_site`, 채점기가 답안 마지막 단계 `calls_next_at`과 대조 | 대상 함수에 닿는 경로가 여러 개(mng_get_long 호출 약 30곳)라 주소만 주면 정답 경로가 정해지지 않음. baseline 2회차가 pHYs 경로를 골라 input 0점 |
| 2026-11-11 | 개발·하네스 실행을 WSL(`~/projects/binary-analysis-agent`)로 이전, 저장소 github.com/be-hum/Binary-Analysis (main). 2026-11-09 Windows 결정을 대체 | 실행되는 것(docker·Ghidra headless·재빌드·nm/objdump)이 전부 리눅스라 wsl.exe 경유·cp949·.cmd 래퍼·WSLENV 문제가 반복됨. 이식성은 `harness/run_task.py`의 `linux()`/`linux_path()`에만 남겨, Windows로 옮길 때 그 두 함수만 본다. Ghidra GUI는 `\wsl$`로 Windows에서 연다 |
