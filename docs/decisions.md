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
| 2026-11-09 | 컨텍스트 구조: CLAUDE.md(항상) + docs/status.md(import) + .claude/rules/(경로별) | 항상 읽히는 분량을 줄이고, 규칙은 해당 파일을 다룰 때만 로드 |
