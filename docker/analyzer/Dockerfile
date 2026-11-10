# analyzer: 평가 대상 에이전트(claude -p)가 도는 컨테이너
#   Ubuntu 24.04 + JDK 21 + Ghidra 12.1 headless + radare2 + binutils + Claude Code
# 규칙: ~/.claude·프로젝트 파일을 이미지에 넣지 않는다. 과제는 실행 시 /work 에 :ro 로만 마운트한다.
FROM ubuntu:24.04

ARG GHIDRA_URL=https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1_build/ghidra_12.1_PUBLIC_20260513.zip
ARG GHIDRA_SHA256=aa5cbcbbf48f41ca185fce900e19592f1ade4cd5994eb6e0ede468dac8a6f302
ARG R2_VERSION=6.2.6
ARG CLAUDE_VERSION=2.1.322

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-21-jdk-headless binutils file xxd python3 \
        ca-certificates curl unzip git ripgrep less procps \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o /tmp/ghidra.zip "$GHIDRA_URL" \
    && echo "$GHIDRA_SHA256  /tmp/ghidra.zip" | sha256sum -c - \
    && unzip -q /tmp/ghidra.zip -d /opt \
    && mv /opt/ghidra_12.1_PUBLIC /opt/ghidra \
    && rm /tmp/ghidra.zip
ENV GHIDRA_HOME=/opt/ghidra
ENV PATH=/opt/ghidra/support:$PATH

RUN curl -fsSL -o /tmp/r2.deb "https://github.com/radareorg/radare2/releases/download/${R2_VERSION}/radare2_${R2_VERSION}_amd64.deb" \
    && apt-get update && apt-get install -y --no-install-recommends /tmp/r2.deb \
    && rm -rf /tmp/r2.deb /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash agent
USER agent
WORKDIR /home/agent
# 설치 과정에서 생기는 ~/.claude* 는 지운다 (실행마다 빈 상태에서 시작)
RUN curl -fsSL https://claude.ai/install.sh | bash -s "$CLAUDE_VERSION" \
    && rm -rf /home/agent/.claude /home/agent/.claude.json
ENV PATH=/home/agent/.local/bin:$PATH
# 자동 업데이트·텔레메트리 등 api.anthropic.com 외 트래픽을 끈다 (egress proxy 가 어차피 막음)
ENV CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1

WORKDIR /work
