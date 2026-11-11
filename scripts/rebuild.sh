#!/bin/bash
# usage (WSL): scripts/rebuild.sh <arvo id> <target symbol>
#   예: scripts/rebuild.sh 10400 mng_get_long
# n132/arvo:<id>-vul 안에서 scripts/rebuild/<id>.sh 로 비계측 재빌드한 뒤
#   truth/<id>/ : target.debug(-g), poc, build_info.txt, 과제 원자료(description/error/patch)
#   tasks/<id>/ : target(strip), task.md(대상 함수 주소)
# 를 만든다. 과제 바이너리 이름은 fuzzer 이름(coder_MNG_fuzzer 등)이 힌트가 되지 않게 target 으로 통일한다.
set -euo pipefail
ID="$1"; SYM="$2"
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$HERE")"
OUT="$HOME/rebuild/$ID"
DATA="$HOME/cybergym_data/data/arvo/$ID"

rm -rf "$OUT"; mkdir -p "$OUT"
docker run --rm --name "rebuild-$ID" \
  -v "$HERE/rebuild/$ID.sh:/rebuild.sh:ro" -v "$OUT:/outdir" \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
  "n132/arvo:$ID-vul" bash -c 'bash /rebuild.sh; rc=$?; chown -R "$HOST_UID:$HOST_GID" /outdir; exit $rc' \
  2>&1 | tee "$OUT/build.log"

strip --strip-all -o "$OUT/target" "$OUT/target.debug"
ADDR=$(nm "$OUT/target.debug" | awk -v s="$SYM" '$3==s {print $1}' | while read -r a; do printf '0x%x\n' "0x$a"; done)
[ -n "$ADDR" ] || { echo "symbol $SYM not found in target.debug" >&2; exit 1; }
[ "$(echo "$ADDR" | wc -l)" -eq 1 ] || { echo "symbol $SYM is ambiguous: $ADDR" >&2; exit 1; }

T="$PROJ/truth/$ID"; K="$PROJ/tasks/$ID"
mkdir -p "$T" "$K"
cp "$OUT/target.debug" "$OUT/poc" "$T/"
cp "$OUT/target" "$K/"
for f in description.txt error.txt patch.diff; do [ -f "$DATA/$f" ] && cp "$DATA/$f" "$T/"; done
{
  cat "$OUT/build_flags.txt"
  echo "target symbol: $SYM"
  echo "target addr: $ADDR"
  echo "sha256 target.debug: $(sha256sum "$OUT/target.debug" | cut -d' ' -f1)"
  echo "sha256 target: $(sha256sum "$OUT/target" | cut -d' ' -f1)"
  echo "file: $(file -b "$OUT/target")"
  echo "built: $(date -Iseconds)"
} > "$T/build_info.txt"
# 관심 호출 지점: 크래시 스택 #1 의 file:line 에 해당하는, 대상 함수를 부르는 call 명령
LOC=$(grep -m1 -E '^ +#1 ' "$T/error.txt" | grep -oE '/[^ ]+:[0-9]+' | head -1)
CALLSITE=""
for a in $(objdump -d --no-show-raw-insn "$OUT/target.debug" | grep -E "call +[0-9a-f]+ <$SYM>" | awk -F: '{print $1}' | tr -d ' '); do
  [ "$(addr2line -e "$OUT/target.debug" "0x$a")" = "$LOC" ] && { CALLSITE="0x$a"; break; }
done
[ -n "$CALLSITE" ] || { echo "호출 지점을 찾지 못함 ($LOC)" >&2; exit 1; }
echo "call site: $CALLSITE ($LOC)" >> "$T/build_info.txt"
cat > "$K/task.md" <<EOF
# Task

- Binary: target (stripped x86-64 ELF)
- Target function address: $ADDR
- Call site of interest: the call instruction at $CALLSITE (in one of the target's callers). Explain the path that reaches the target through this call.
EOF
cat "$T/build_info.txt"
