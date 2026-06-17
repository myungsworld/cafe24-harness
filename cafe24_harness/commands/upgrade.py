"""cf upgrade — cafe24-harness 를 최신으로 (pipx). 쿨다운·비차단·실패무시.

SessionStart 훅이 `cf upgrade --quiet --cooldown 21600` 형태로 호출한다.
실제 업그레이드는 쿨다운이 지났을 때만 시도하고, 어떤 실패도 조용히 넘긴다.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

CAFE24_HOME = Path.home() / ".cafe24"
STAMP = CAFE24_HOME / ".last-upgrade"
FALLBACK_SPEC = "git+https://github.com/myungsworld/cafe24-harness"


def _install_spec() -> str:
    """pipx 메타데이터에서 설치 spec(git URL 등)을 읽는다. 없으면 fallback."""
    meta = Path.home() / ".local" / "pipx" / "venvs" / "cafe24-harness" / "pipx_metadata.json"
    try:
        d = json.loads(meta.read_text(encoding="utf-8"))
        spec = (d.get("main_package") or {}).get("package_or_url")
        if spec:
            return spec
    except Exception:
        pass
    return FALLBACK_SPEC


def _within_cooldown(seconds: int) -> bool:
    if seconds <= 0 or not STAMP.exists():
        return False
    return (time.time() - STAMP.stat().st_mtime) < seconds


def _touch() -> None:
    CAFE24_HOME.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(str(int(time.time())), encoding="utf-8")


def run(args) -> int:
    quiet = getattr(args, "quiet", False)
    cooldown = getattr(args, "cooldown", 0)
    force = getattr(args, "force", False)

    def say(msg):
        if not quiet:
            print(msg)

    if not force and _within_cooldown(cooldown):
        say("cafe24-harness: 쿨다운 중 — 업그레이드 스킵")
        return 0

    pipx = shutil.which("pipx")
    if not pipx:
        say("pipx 없음 — 수동: pipx upgrade cafe24-harness")
        return 0

    try:
        # git 설치는 pipx upgrade 가 HEAD를 재-fetch 안 하는 경우가 있어 강제 재설치한다.
        r = subprocess.run(
            [pipx, "install", "--force", "--pip-args=--no-cache-dir", _install_spec()],
            capture_output=True, text=True, timeout=180,
        )
        _touch()  # 시도했으면 쿨다운 갱신(성공/무변화 무관)
        out = (r.stdout + r.stderr).strip().splitlines()
        say(out[-1] if out else "cafe24-harness: 최신 상태")
    except Exception as e:  # 네트워크/타임아웃 등 — 절대 세션 막지 않음
        say(f"cafe24-harness upgrade 스킵(실패): {e}")

    # 후처리: Claude Code 자산(슬래시 명령어·에이전트) 갱신 — 전파의 마지막 단계. 실패무시.
    try:
        from . import claude as _claude
        _claude.install(args)
    except Exception as e:
        say(f"(claude 자산 갱신 스킵: {e})")
    return 0
