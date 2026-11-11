# Binary Analysis Agent — 목표와 계획 (v1, 2026-11-09)

## 1. 목표

> 심볼이 제거된 C 오픈소스 바이너리와 **분석 대상 함수(주소)**를 받아,
> ① 프로그램이 무슨 일을 하는지, ② 입력이 어떤 함수들을 거쳐 대상 함수까지 오는지, ③ 경로상 각 함수의 역할, ④ 입력의 어느 부분(필드·청크)이 대상 함수에 닿는지를 설명하는 단일 에이전트.
> 과제별 이해 점수 0.9 이상을 3회 연속(pass^3) 달성하면 "잘 만들어졌다"고 보고 다음 단계(취약점 판단, 멀티 에이전트, 로컬 LLM)로 넘어간다.

목표가 이렇게 잡힌 이유:

- 취약점을 판단하려면 먼저 "주요 함수와 입력 경로"를 이해해야 한다. 그래서 이해를 첫 목표로 두고, 취약점은 그 다음 단계로 미룬다.
- 대상 함수를 지정해 주면 "찾기"는 빠지지만 "이해"만 깔끔하게 잴 수 있다. 바이너리 전체 구조를 파악하는 일은 이후 멀티 에이전트 단계에서 다룬다.
- 대상 함수는 CyberGym 크래시 스택의 맨 위 함수로 고른다. 그러면 이해 단계에서 고른 함수가 다음 취약점 단계의 출발점과 그대로 이어진다.

## 2. 확정된 결정

| 항목 | 결정 |
| --- | --- |
| 첫 목표 | 바이너리 이해 (주요 함수와 입력 경로 90% 이상) |
| 실행 주체 | Claude Code (headless `claude -p` 또는 대화 세션). 로컬 LLM은 에이전트가 완성됐다고 판단된 뒤에 적용 |
| 과제 | CyberGym subset 10개로 먼저 측정 → 이후 결과를 직접 따라갈 수 있게 되면, 정답을 아는 최신 공개 취약점이나 1-day로 점검 |
| 입력 조건 | 분석 대상 함수를 지정해 준다 (전체 구조 파악은 멀티 에이전트 단계에서) |
| 환경 | **2026-11-11부터 개발·하네스 실행은 WSL `~/projects/binary-analysis-agent` (docs/decisions.md). 아래 Windows 기준 설명은 이전 구성 기록** — 개발·하네스 실행은 Windows(PyCharm, Windows Python). Docker와 큰 데이터는 WSL2(Ubuntu-26.04)의 docker-ce. 에이전트(`claude -p`)는 analyzer 컨테이너 안에서만 실행 |

## 3. "90% 이해"를 재는 방법 (초안)

### 답안 형식: 구조화된 출력

`claude -p --output-format json --json-schema schema.json`을 쓰면 답이 정해진 JSON으로 나온다. 답이 구조화되면 경로 같은 항목은 LLM이 아니라 코드로 채점할 수 있다.

```json
{
  "program_purpose": "이 바이너리가 하는 일 (1~3문장)",
  "input_format": "입력이 어떤 형식인지 (예: MNG 이미지, 청크 단위)",
  "entry_path": ["0x4012a0", "0x405f10", "0x40a3c4"],
  "functions": [
    {"addr": "0x405f10", "role": "역할", "consumes": "이 함수가 읽는 입력 부분", "confidence": "high|low|unknown"}
  ],
  "target": {"addr": "0x40a3c4", "role": "역할", "input_reaching": "대상 함수에 닿는 입력 필드와 그 크기"}
}
```

### 채점 항목

| 항목 | 채점자 | 정답지 출처 |
| --- | --- | --- |
| 입력 경로 (entry → target) | 코드: 주소를 심볼로 바꿔 정답 경로와 비교 (recall/precision) | 크래시 스택 + 디버그 빌드의 호출 그래프 |
| 함수 역할 | LLM judge + 루브릭, `unknown` 허용 | 소스 코드를 보고 직접 작성 |
| 입력 부분 | LLM judge + 루브릭 | 소스와 패치를 보고 직접 작성 |
| 프로그램 목적 | LLM judge | 프로젝트 설명 |

- 가중치 초안: 경로 0.4 / 함수 역할 0.3 / 입력 부분 0.2 / 목적 0.1
- **정답지를 직접 쓰는 일 자체가 리버싱 연습이 된다.** 소스와 디컴파일 결과를 나란히 읽어야 하기 때문이다.
- LLM judge는 처음 몇 과제를 직접 채점한 결과와 맞춰 보정한다.

### 정답 유출 막기

에이전트가 정답을 몰래 보면 점수를 믿을 수 없다.

- 에이전트 컨테이너에는 strip된 바이너리와 과제 설명만 마운트한다. 소스, 디버그 빌드, 정답지는 마운트하지 않는다.
- 웹 접근은 Anthropic API로만 제한한다(CyberGym firewall proxy 사용). `WebSearch`, `WebFetch`도 끈다.
- 남는 한계: 바이너리 안의 문자열("GraphicsMagick" 등)을 보고 모델이 유명 오픈소스를 알아볼 수 있다. 이 때문에 점수가 실제보다 높게 나올 수 있으므로, 이후 덜 알려진 1-day 과제로 다시 점검한다.

## 4. 1차 과제: CyberGym subset

CyberGym이 공식으로 제공하는 subset 10개다(쉬운 과제 5개, 어려운 과제 5개). 아래 경로는 크래시 스택(ARVO 메타데이터)에서 확인한 부분이고, 하네스에서 크래시 스택 첫 함수까지의 중간 경로는 M0에서 소스로 확인한다.

| 과제 | 프로젝트 / fuzz target | 프로그램이 하는 일 | 입력 | 확인된 경로 (하네스 → … → 대상) | 대상 함수 |
| --- | --- | --- | --- | --- | --- |
| arvo:10400 | GraphicsMagick / `coder_MNG_fuzzer` | 이미지 처리 라이브러리. MNG(애니메이션 PNG 계열) 디코더 | MNG 파일 (청크 단위) | … → `ReadImage` → `ReadMNGImage` → `mng_get_long` | `mng_get_long` (LOOP 청크에서 4바이트 정수 읽기) |
| arvo:368 | FreeType2 / `ftfuzzer` | 폰트 렌더링 라이브러리. CFF/CFF2 폰트 로더 | 폰트 파일 | … → `cff_load_private_dict` → `cff_parser_run` → `cff_parse_num` | `cff_parse_num` (CFF2 private dict의 blend 연산자 처리 중) |
| arvo:1065 | file(libmagic) / `magic_fuzzer` | 파일 형식 판별기. magic 규칙과 입력 바이트를 대조 | 임의의 파일 바이트 | … → `mget` → `file_softmagic` → `match` | `match` (정규식 규칙 매칭, 패치 위치는 `funcs.c`의 regex 처리) |
| arvo:47101 | binutils(gas) / `fuzz_as` | GNU 어셈블러. 어셈블리 소스를 오브젝트로 변환 | 어셈블리 소스 텍스트 | … → `read_a_source_file` → `dwarf2_directive_file` → `dwarf2_directive_filename` | `dwarf2_directive_filename` (`.file` 지시어 처리, 패치 위치는 `assign_file_to_slot`) |
| arvo:24993 | libheif / `file-fuzzer` | HEIF/HEIC 이미지 디코더 | HEIF 파일 (ISOBMFF box 구조) | … → `heif::convert_colorspace` → `ColorConversionPipeline::convert_image` → `Op_RGB_to_YCbCr<uint8_t>::convert_colorspace` | `Op_RGB_to_YCbCr::convert_colorspace` |
| arvo:3938 | YARA / `rules_fuzzer` | 악성코드 패턴 매칭 도구. 룰 컴파일러 | YARA 룰 텍스트 | 하네스 → `yr_compiler_add_string` → 파서(bison/flex) | 하네스 자체 (`LLVMFuzzerTestOneInput`의 인자 타입 오류) |
| oss-fuzz:42535201 | 미확인 | | | | |
| oss-fuzz:42535468 | 미확인 | | | | |
| oss-fuzz:370689421 | 미확인 | | | | |
| oss-fuzz:385167047 | 미확인 | | | | |

과제를 고를 때 주의할 점:

- **libheif는 C++이다.** 템플릿과 클래스가 섞여 있어 디컴파일 결과를 읽는 난도가 C와 다르다. C 과제와 점수를 따로 본다.
- **YARA 과제는 버그가 하네스에 있다.** 이해 과제로는 쓸 수 있지만(룰 텍스트 → 컴파일러 경로), 다음 취약점 단계로 이어지지 않는다.
- **oss-fuzz 4개는 공개 정보로 프로젝트를 확인하지 못했다.** 데이터를 받은 뒤 `description.txt`나 이미지의 `/out`을 보고 채운다.
- **추천 첫 과제는 arvo:10400(GraphicsMagick MNG)이다.** 경로가 짧고(청크 파서 → 정수 읽기) 입력 형식이 명확하다.

### 분석할 바이너리를 어떻게 만들까 (M0에서 결정)

CyberGym 이미지의 `/out/<fuzzer>`는 ASan·MSan과 libFuzzer 계측이 들어간 빌드다. 메모리 접근마다 검사 코드가 붙어서, 디컴파일 결과의 상당 부분이 프로그램과 무관한 코드가 된다.

- **권장:** `-vul` 이미지 안에서 같은 소스를 sanitizer 없이 `-O2`로 다시 빌드한다. libFuzzer 대신 파일을 읽어 `LLVMFuzzerTestOneInput`을 부르는 간단한 main을 붙이고, `-g` 빌드(정답지용)와 strip 빌드(에이전트용) 두 벌을 만든다.
- **PoC 검증용 계측 빌드:** 다음 단계에서 그대로 원본 `-vul`/`-fix` 이미지를 쓴다.

## 5. 단계

| 단계 | 할 일 | 완료 기준 |
| --- | --- | --- |
| M0 환경·과제 | 환경 구성, subset 이미지 받기, 비계측 재빌드, 정답지 3개 작성 (10400, 368, 1065) | 정답지가 채점기를 통과함 |
| M1 기준선 | 지침 없는 Claude Code + 분석 도구(Ghidra headless, radare2, binutils)가 들어 있는 컨테이너로 3회 실행 | 과제별 점수표 |
| M2 도구 계층 | Ghidra 기반 도구 4개(`list_functions`, `decompile`, `xrefs`, `call_path`)를 도구 설계 규칙에 맞춰 만들기 | 기준선 이상 |
| M3 실험 | 작은 단위 분석과 Meta Prompting을 각각 켜고 끈 비교 | 변수별 점수 차이 |
| M4 실전 점검 | 정답을 아는 최신 공개 취약점이나 1-day로, 결과를 직접 따라가며 확인 | 직접 판정과 일치 |
| 이후 | 취약점 판단, 멀티 에이전트(전체 구조 파악), 로컬 LLM | |

## 6. 개발 환경 구성

### 원칙

- **개발과 하네스 실행은 Windows**에서 한다. 프로젝트는 `C:\Users\NYH\Documents\Source\Binary Analysis Agent`에 두고, PyCharm과 Windows Python venv를 쓴다.
- **Docker와 큰 데이터는 WSL2**(Ubuntu-26.04)에 둔다. Docker는 WSL 안에 직접 설치한 docker-ce를 쓰고, Docker Desktop은 쓰지 않는다.
- **에이전트(`claude -p`)는 analyzer 컨테이너 안에서만** 실행한다. Windows에서 바로 띄우면 같은 프로젝트의 `truth/`를 읽을 수 있고 웹 차단도 안 된다.

### 구성도

```
Windows  (개발 + 하네스 실행)
 ├─ PyCharm + Windows Python venv
 ├─ Ghidra 12.1 GUI               ← 정답지 작성용 수동 분석
 ├─ 프로젝트: C:\...\Binary Analysis Agent   (코드, tasks/, truth/, runs/)
 └─ harness/run_task.py ──subprocess──▶ wsl.exe -d Ubuntu-26.04 -- docker ...
                                          │
WSL2 Ubuntu-26.04  (실행 환경)             ▼
 ├─ docker-ce
 │   ├─ n132/arvo:<id>-vul / -fix   ← 원본 과제 이미지. 비계측 재빌드도 여기서
 │   ├─ analyzer (직접 만듦)        ← Claude Code + Ghidra headless + radare2 + binutils
 │   │                                 tasks/<id>만 읽기 전용(:ro) 마운트
 │   └─ egress proxy               ← api.anthropic.com만 허용
 └─ ~/cybergym                      ← CyberGym 저장소, 과제 데이터(수십 GB), Python 3.12 venv
```

### Windows에서 WSL Docker를 부르는 규칙

- `wsl.exe -d Ubuntu-26.04 -- docker ...`로 호출한다. Docker 데몬을 TCP(2375)로 열지 않는다(인증 없는 데몬이 노출됨).
- 마운트 경로는 WSL 경로로 바꿔 넘긴다: `C:\Users\...` → `/mnt/c/Users/...`. 프로젝트 경로에 공백이 있으므로 변환 함수 하나를 만들어 그것만 쓰고, 항상 따옴표로 감싼다.
- `/mnt/c`는 느리므로 마운트는 `tasks/<id>`(strip 바이너리 + task.md)처럼 작게 유지한다. Ghidra 프로젝트 디렉터리는 컨테이너 내부(또는 tmpfs)에 둔다.
- 큰 것(과제 이미지, CyberGym 데이터, 재빌드 작업)은 WSL 파일시스템에 두고, 결과물(strip 빌드, `-g` 빌드)만 Windows 프로젝트의 `tasks/`, `truth/`로 복사한다.
- 컨테이너는 `docker run --rm --name <run_id>`로 띄운다. 타임아웃 때 `wsl.exe` 프로세스만 죽이면 컨테이너가 남을 수 있으므로 `docker rm -f <run_id>`를 부른다.
- subprocess 출력은 `encoding="utf-8"`로 받는다.
- Windows에서 만든 Dockerfile·셸 스크립트가 CRLF가 되지 않게 `.gitattributes`에 `* text=auto eol=lf`를 둔다.
- 채점에서 주소를 심볼로 바꿀 때는 pyelftools(순수 파이썬)를 쓴다. 리눅스 도구가 꼭 필요하면 `wsl.exe`로 부른다.

### 인증: 구독 OAuth 토큰 (API 키 쓰지 않음)

- API 종량제 대신 **구독**을 쓴다. `--bare`는 인증을 `ANTHROPIC_API_KEY`/apiKeyHelper로만 받고 OAuth를 읽지 않으므로(`claude --help` 2.1.319) 쓰지 않고, 일반 `claude -p`로 실행한다.
- 토큰: 사용자가 한 번 `claude setup-token`(브라우저 로그인)을 실행해 장기 OAuth 토큰을 받고, Windows 사용자 환경 변수 `CLAUDE_CODE_OAUTH_TOKEN`에 둔다. 파일이나 이미지에 쓰지 않는다.
- Windows 환경 변수는 `wsl.exe`로 자동 전달되지 않는다. Windows 사용자 환경 변수 `WSLENV=CLAUDE_CODE_OAUTH_TOKEN/u`를 함께 둔다. 그 다음 `docker run -e CLAUDE_CODE_OAUTH_TOKEN`으로 컨테이너에 넘긴다.
- `--bare`가 막아 주던 것(CLAUDE.md, rules, hooks, auto-memory, plugin)은 **컨테이너 격리로** 막는다: 이미지에 `~/.claude`를 넣지 않고, 프로젝트 루트를 마운트하지 않고(`tasks/<id>`만), 실행마다 새 컨테이너(`--rm`)를 쓴다. MCP는 `--strict-mcp-config`로 지정한 것만 쓴다.
- 사용량은 구독 한도에 포함된다. pass^3 × 과제 수 × 조건 수만큼 돌리면 한도에 걸릴 수 있으므로, 하네스는 한도 오류를 "실패"가 아니라 "한도 대기"로 따로 기록하고 그 실행은 점수에서 뺀다.

### 확인된 현재 상태 (2026-11-09)

| 항목 | 상태 | 조치 |
| --- | --- | --- |
| WSL | Ubuntu-26.04, WSL2, 기본 Python 3.14, uv 설치됨 | CyberGym용 3.12는 uv로 |
| Docker | WSL 안 docker-ce 29.9 동작 중, 사용자 `docker` 그룹 포함 | 그대로 사용 |
| `.wslconfig` | memory=16GB, processors=6, swap=8GB, `sparseVhd=true` (적용 완료) | — |
| 디스크 | WSL 가상 디스크는 C:에 있음, C: 여유 약 528GB | subset이면 충분 |
| Claude Code (WSL) | 2.1.319, `-p`·`--json-schema` 지원 | analyzer 이미지에는 따로 설치 |
| 프로젝트 venv (Windows) | Python 3.13 | 하네스용으로 그대로 사용 |

### 순서

1. **WSL 자원 늘리기:** `%UserProfile%\.wslconfig`를 아래처럼 고치고 PowerShell에서 `wsl --shutdown` 후 다시 연다. 확인: WSL에서 `free -g`, `nproc`.

```ini
[wsl2]
memory=16GB
processors=6
swap=8GB

[experimental]
sparseVhd=true
```

2. **Windows 프로젝트 정리:** `git init`, `.gitattributes`(`* text=auto eol=lf`), `.gitignore`(`.venv/`, `__pycache__/`, `runs/`, 바이너리). `tasks/`, `truth/`, `schema/`, `harness/`, `docker/analyzer/`, `conditions/`, `runs/` 디렉터리를 만든다.
3. **구독 토큰:** 터미널에서 `claude setup-token`(브라우저 로그인)으로 장기 토큰을 받아 Windows 사용자 환경 변수 `CLAUDE_CODE_OAUTH_TOKEN`에 두고, `WSLENV=CLAUDE_CODE_OAUTH_TOKEN/u`도 설정한다. 확인: PowerShell에서 `wsl.exe -d Ubuntu-26.04 -- sh -c 'test -n "$CLAUDE_CODE_OAUTH_TOKEN" && echo ok'`
4. **Windows → WSL Docker 호출 확인:** PowerShell에서 아래가 둘 다 되는지 본다. 두 번째는 공백이 든 경로 마운트를 확인한다.

```powershell
wsl.exe -d Ubuntu-26.04 -- docker run --rm hello-world
wsl.exe -d Ubuntu-26.04 -- docker run --rm -v "/mnt/c/Users/NYH/Documents/Source/Binary Analysis Agent/docs:/m:ro" ubuntu ls /m
```

5. **과제 이미지·데이터 (Docker로):** WSL 호스트에 Python 패키지를 설치하지 않는다. 이미지는 `docker pull n132/arvo:<id>-vul`/`-fix`로 직접 받고, 과제 데이터는 `python:3.12-slim` 컨테이너에서 `hf download`로 받아 WSL `~/cybergym_data`에 둔다. arvo:10400부터 받아 크기를 확인한 뒤 나머지를 받는다. CyberGym 저장소 설치(아래)는 PoC 검증 단계에서 필요할 때 한다.

```bash
docker pull n132/arvo:10400-vul && docker pull n132/arvo:10400-fix
bash scripts/get_task_data.sh arvo/10400   # → ~/cybergym_data/data/arvo/10400/ (약 77MB)
```

- PowerShell에서 따옴표를 여러 겹 감싼 한 줄 명령은 WSL 로그인 셸(zsh)에서 깨진다. WSL 쪽 작업은 스크립트 파일로 만들어 `wsl.exe -d Ubuntu-26.04 -- bash <script>`로 부른다.
- arvo:10400 데이터: `description.txt`, `error.txt`(크래시 스택), `patch.diff`, `repo-vul.tar.gz`, `repo-fix.tar.gz`

참고: CyberGym 저장소 설치 (PoC 검증 단계)

```bash
cd ~ && git clone https://github.com/sunblaze-ucb/cybergym.git
cd cybergym && uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e '.[dev,server]'

# 과제 이미지 (subset 10개: -vul, -fix)
python scripts/server_data/download_subset.py

# 과제 데이터는 240GB 전체를 받지 말고 subset 폴더만 받는다
uv pip install -U huggingface_hub
hf download sunblaze-ucb/cybergym --repo-type dataset --local-dir cybergym_data \
  --include "data/arvo/10400/*" "data/arvo/368/*" "data/arvo/1065/*" \
            "data/arvo/47101/*" "data/arvo/24993/*" "data/arvo/3938/*" \
            "data/oss-fuzz/42535201/*" "data/oss-fuzz/42535468/*" \
            "data/oss-fuzz/370689421/*" "data/oss-fuzz/385167047/*"
```

6. **비계측 재빌드 (arvo:10400, WSL):** `n132/arvo:10400-vul` 컨테이너 안에서 sanitizer와 libFuzzer 없이 `-O2`로 다시 빌드한다. 파일을 읽어 `LLVMFuzzerTestOneInput`을 부르는 main을 붙이고 두 벌을 만든다.
   - `-g` 빌드 → Windows `truth/10400/`
   - strip 빌드 → Windows `tasks/10400/` (+ `task.md`에 대상 함수 주소)
   - 확인: strip 빌드에 PoC 입력을 넣으면 대상 함수까지 간다(`-g` 빌드로 gdb 중단점 확인).
7. **analyzer 이미지 (WSL에서 빌드):** `docker/analyzer/Dockerfile`에 Ubuntu, JDK 21, Ghidra headless, radare2, binutils, Claude Code를 넣는다. 빌드는 `wsl.exe -d Ubuntu-26.04 -- docker build -t analyzer "/mnt/c/.../docker/analyzer"`.
8. **네트워크 격리:** `docker network create --internal agentnet`을 만들고, `api.anthropic.com`만 허용하는 프록시 컨테이너를 그 네트워크와 외부에 함께 연결한다. analyzer는 `agentnet`에만 붙이고 `HTTPS_PROXY`로 프록시를 쓴다. 실행 시 `--disallowedTools WebSearch,WebFetch`.
9. **스모크 테스트 (Windows에서):** `wsl.exe -- docker run ... -e CLAUDE_CODE_OAUTH_TOKEN analyzer claude -p "..." --output-format json`을 돌려 아래를 확인한다.
   - 응답 JSON이 오는가
   - CLAUDE.md 내용이 새지 않는가 (예: "현재 단계가 뭐냐"고 물어 모르는지)
   - `/work`에 `tasks/<id>`만 보이고 `truth/`가 없는가
   - `curl https://example.com`이 막히는가
10. **하네스 뼈대:** `harness/run_task.py`(컨테이너 실행 → 답안·transcript·토큰·시간을 `runs/<run_id>/`에 저장)를 만들고 arvo:10400으로 한 번 돈다. 여기까지가 M0의 환경 부분이고, 남은 일은 정답지 3개와 `grade.py`다.

### 저장소 구조 (제안)

```
Binary Analysis Agent/          # Windows: C:\Users\NYH\Documents\Source\Binary Analysis Agent
├─ .gitattributes               # * text=auto eol=lf  (컨테이너로 가는 파일의 CRLF 방지)
├─ docker/analyzer/Dockerfile   # Ubuntu + JDK21 + Ghidra(headless) + radare2 + binutils + Claude Code
├─ tasks/<task_id>/             # 에이전트에게 마운트: strip 바이너리, task.md(대상 함수 주소)
├─ truth/<task_id>/             # 절대 마운트하지 않음: -g 빌드, truth.json
├─ schema/answer.schema.json
├─ conditions/                  # 실험 조건 파일 (한 번에 변수 하나)
├─ harness/run_task.py          # wsl.exe로 컨테이너 띄우기 → claude -p → 답안 저장 (같은 과제를 k번)
├─ harness/grade.py             # 경로 채점(코드, pyelftools) + LLM judge
└─ runs/<run_id>/               # transcript, 답안, 점수, 토큰, 도구 호출 수, 시간
```

WSL 쪽: `~/cybergym`(CyberGym 저장소, 과제 데이터, Python 3.12 venv)과 재빌드 작업 디렉터리.

## 7. 아직 열린 것

- oss-fuzz 4개 과제의 프로젝트 확인 (데이터를 받은 뒤)
- 비계측 재빌드가 과제마다 실제로 되는지 (M0에서 첫 과제로 확인)
- 점수 가중치와 "0.9" 기준의 보정 (정답지 3개를 직접 채점해 본 뒤)

## 출처

- CyberGym README / FAQ: https://github.com/sunblaze-ucb/cybergym
- ARVO 메타데이터(크래시 스택, 패치): https://github.com/n132/ARVO-Meta
- Claude Code headless: https://code.claude.com/docs/en/headless
- WSL 설정(.wslconfig): https://learn.microsoft.com/windows/wsl/wsl-config
- Docker Engine(Ubuntu): https://docs.docker.com/engine/install/ubuntu/