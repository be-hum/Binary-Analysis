#!/bin/bash
# arvo:10400 (GraphicsMagick coder_MNG_fuzzer) 비계측 재빌드. n132/arvo:10400-vul 컨테이너 안에서 실행된다.
# 원본: /src/graphicsmagick/fuzzing/oss-fuzz-build.sh — 의존 라이브러리 순서·옵션은 그대로 두고
# sanitizer·libFuzzer만 빼고, 최적화는 -O2 -fno-inline (docs/decisions.md 2026-11-10).
# 결과: /outdir/target.debug (-g, 심볼 있음), /outdir/poc, /outdir/build_flags.txt
set -euo pipefail

export CC=clang CXX=clang++
export CFLAGS="-O2 -fno-inline -g -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION"
export CXXFLAGS="$CFLAGS"
unset SANITIZER LIB_FUZZING_ENGINE
# 이미지의 /work 에는 ASan 빌드 산출물이 있으므로 섞이지 않게 새 디렉터리를 쓴다
export WORK=/build
mkdir -p "$WORK"
NJ=$(nproc)

pushd "$SRC/zlib"
./configure --prefix="$WORK"
make -j"$NJ" CFLAGS="$CFLAGS -fPIC"
make install
popd

pushd "$SRC/libpng"
cmake . -DCMAKE_INSTALL_PREFIX="$WORK"
make -j"$NJ"
make install
popd

pushd "$SRC/libtiff"
autoreconf -fiv
./configure --prefix="$WORK"
make -j"$NJ"
make install
popd

pushd "$SRC/Little-CMS"
autoreconf -fiv
./configure --prefix="$WORK"
make -j"$NJ"
make install
popd

pushd "$SRC/freetype2"
./autogen.sh
./configure --prefix="$WORK" PKG_CONFIG_PATH="$WORK/lib/pkgconfig"
make -j"$NJ"
make install
popd

pushd "$SRC/libwebp"
./autogen.sh
./configure --enable-libwebpmux --prefix="$WORK" CFLAGS="$CFLAGS -fPIC"
make -j"$NJ"
make install
popd

cd "$SRC/graphicsmagick"
./configure --prefix="$WORK" PKG_CONFIG_PATH="$WORK/lib/pkgconfig" CFLAGS="$CFLAGS -I$WORK/include" LDFLAGS="-L$WORK/lib"
make -j"$NJ"
make install

MAGICK_LIBS="$WORK/lib/libz.a $WORK/lib/libpng.a $WORK/lib/libtiff.a $WORK/lib/liblcms2.a $WORK/lib/libwebpmux.a $WORK/lib/libwebp.a $WORK/lib/libfreetype.a"

# libFuzzer 대신 파일을 읽어 LLVMFuzzerTestOneInput 을 부르는 표준 main
$CC $CFLAGS -c "$SRC/libfuzzer/standalone/StandaloneFuzzTargetMain.c" -o /tmp/standalone_main.o

# coder_list 가 +MNG 를 내므로 원본과 같이 WRITE=1
$CXX $CXXFLAGS -std=c++11 -I "$WORK/include/GraphicsMagick" \
    fuzzing/coder_fuzzer.cc /tmp/standalone_main.o -o /outdir/target.debug \
    -DFUZZ_GRAPHICSMAGICK_CODER=MNG -DFUZZ_GRAPHICSMAGICK_CODER_WRITE=1 \
    "$WORK/lib/libGraphicsMagick++.a" "$WORK/lib/libGraphicsMagick.a" $MAGICK_LIBS \
    -lpthread -lm  # 원본은 ASan 런타임이 pthread 를 끌어왔으므로 명시 필요

cp /tmp/poc /outdir/poc
{
  echo "image: n132/arvo:10400-vul"
  echo "graphicsmagick hg: $(hg id 2>/dev/null || echo unknown)"
  echo "CC: $($CC --version | head -1)"
  echo "CFLAGS: $CFLAGS"
  echo "harness: fuzzing/coder_fuzzer.cc -DFUZZ_GRAPHICSMAGICK_CODER=MNG -DFUZZ_GRAPHICSMAGICK_CODER_WRITE=1 + StandaloneFuzzTargetMain.c"
} > /outdir/build_flags.txt
