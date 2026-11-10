#!/bin/bash
# usage (WSL): scripts/env_up.sh
# analyzer·egress 이미지를 빌드하고, 내부 네트워크 agentnet 과 egress 프록시를 띄운다. 여러 번 실행해도 된다.
#   agentnet (--internal): 바깥으로 나가는 경로 없음. analyzer 는 여기에만 붙는다
#   egress: agentnet + bridge 양쪽에 붙은 tinyproxy. api.anthropic.com:443 만 통과
# analyzer 실행 예:
#   docker run --rm --network agentnet -e HTTPS_PROXY=http://egress:8888 -e CLAUDE_CODE_OAUTH_TOKEN \
#     -v "<tasks/id 경로>:/work:ro" analyzer claude -p "..."
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJ="$(dirname "$HERE")"

docker build -t analyzer "$PROJ/docker/analyzer"
docker build -t egress "$PROJ/docker/egress"

docker network inspect agentnet >/dev/null 2>&1 || docker network create --internal agentnet
docker rm -f egress >/dev/null 2>&1 || true
docker run -d --name egress --restart unless-stopped --network bridge egress >/dev/null
docker network connect agentnet egress
echo "analyzer/egress built, agentnet + egress up"
