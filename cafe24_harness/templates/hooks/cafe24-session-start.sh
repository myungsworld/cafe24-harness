#!/bin/sh
# cafe24-harness SessionStart 훅.
# cf init 된 프로젝트(admin/config.yaml 존재)에서 Claude 세션이 열릴 때마다 실행되어,
# cf upgrade 를 백그라운드로 호출한다(실제 네트워크 업그레이드는 cf 내부 쿨다운으로 제한).
# 비차단·실패무시: 어떤 경우에도 세션 시작을 막지 않는다.

dir="${CLAUDE_PROJECT_DIR:-$PWD}"

# 스코프 게이트: cf init 된 프로젝트에서만
if [ ! -f "$dir/admin/config.yaml" ] && [ ! -f "$dir/config.yaml" ]; then
  exit 0
fi

# cf 위치 탐색 (PATH → ~/.local/bin)
CF="$(command -v cf 2>/dev/null)"
if [ -z "$CF" ] && [ -x "$HOME/.local/bin/cf" ]; then
  CF="$HOME/.local/bin/cf"
fi

# 백그라운드 실행 (쿨다운 6시간). 세션 시작을 절대 막지 않음.
if [ -n "$CF" ]; then
  (nohup "$CF" upgrade --quiet --cooldown 21600 >/dev/null 2>&1 &)
fi

exit 0
