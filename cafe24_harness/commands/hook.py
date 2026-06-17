"""cf hook install|uninstall — SessionStart 자동 업그레이드 훅을 ~/.claude 에 등록/해제.

cf init 된 프로젝트에서 Claude 세션이 열릴 때마다 cf upgrade(쿨다운)가 돌도록
글로벌 ~/.claude/settings.json 의 SessionStart 에 훅을 멱등 등록한다.
"""
from __future__ import annotations

import json
import stat
from importlib import resources
from pathlib import Path

HOOK_NAME = "cafe24-session-start.sh"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS = CLAUDE_DIR / "settings.json"
HOOK_CMD = f"~/.claude/hooks/{HOOK_NAME}"


def _install_script() -> Path:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    src = (resources.files("cafe24_harness") / "templates" / "hooks" / HOOK_NAME).read_text(encoding="utf-8")
    dest = HOOKS_DIR / HOOK_NAME
    dest.write_text(src, encoding="utf-8")
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def _load_settings() -> dict:
    if SETTINGS.exists():
        try:
            return json.loads(SETTINGS.read_text(encoding="utf-8"))
        except Exception:
            print(f"⚠️ {SETTINGS} 파싱 실패 — 손대지 않고 중단")
            raise
    return {}


def _save_settings(data: dict) -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _session_start(data: dict) -> list:
    return data.setdefault("hooks", {}).setdefault("SessionStart", [])


def _has_hook(data: dict) -> bool:
    for grp in data.get("hooks", {}).get("SessionStart", []):
        for h in grp.get("hooks", []):
            if h.get("command") == HOOK_CMD:
                return True
    return False


def install(args) -> int:
    dest = _install_script()
    data = _load_settings()
    if _has_hook(data):
        print(f"· SessionStart 훅 이미 등록됨: {HOOK_CMD}")
    else:
        _session_start(data).append({"hooks": [{"type": "command", "command": HOOK_CMD}]})
        _save_settings(data)
        print(f"＋ SessionStart 훅 등록: {HOOK_CMD}")
    print(f"  스크립트: {dest}")
    print("→ 이제 cf init 된 프로젝트에서 세션 열 때마다 cf upgrade(쿨다운 6h)가 백그라운드 실행됩니다.")
    return 0


def uninstall(args) -> int:
    data = _load_settings()
    ss = data.get("hooks", {}).get("SessionStart", [])
    new = []
    removed = False
    for grp in ss:
        kept = [h for h in grp.get("hooks", []) if h.get("command") != HOOK_CMD]
        if len(kept) != len(grp.get("hooks", [])):
            removed = True
        if kept:
            grp["hooks"] = kept
            new.append(grp)
    if removed:
        data["hooks"]["SessionStart"] = new
        _save_settings(data)
        print("훅 해제됨")
    else:
        print("등록된 cafe24 훅 없음")
    p = HOOKS_DIR / HOOK_NAME
    if p.exists():
        p.unlink()
    return 0


def run(args) -> int:
    if args.hook_action == "install":
        return install(args)
    if args.hook_action == "uninstall":
        return uninstall(args)
    print("usage: cf hook {install|uninstall}")
    return 1
