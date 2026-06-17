"""cf — 카페24 어드민 하네스 CLI 디스패처."""
from __future__ import annotations

import argparse
import subprocess
import sys

from . import __version__


def _cmd_setup(args) -> int:
    print("chromium 설치 중... (playwright install chromium)")
    return subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cf", description="카페24 어드민 자기개선 하네스")
    p.add_argument("--version", action="version", version=f"cafe24-harness {__version__}")
    sub = p.add_subparsers(dest="cmd")

    pi = sub.add_parser("init", help="프로젝트에 설정 스캐폴드 (멱등)")
    pi.add_argument("--mall", help="몰 도메인 (예: yourmall.cafe24.com)")
    pi.add_argument("--shop", help="shop_id (기본 shop1)")
    pi.add_argument("--board", type=int, help="리뷰 게시판 번호")
    pi.add_argument("--dir", default="admin", help="설정 디렉토리 (기본 admin)")
    pi.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    pi.add_argument("--migrate", action="store_true", help="구버전 selectors에서 설정 추출/정리")
    pi.add_argument("--no-hook", action="store_true", help="SessionStart 자동업그레이드 훅 등록 생략")

    pl = sub.add_parser("login", help="headed 브라우저로 직접 로그인 → 세션 저장")
    pl.add_argument("--dir", default=None)

    pin = sub.add_parser("inspect", help="화면 진단")
    isub = pin.add_subparsers(dest="target")
    pb = isub.add_parser("board", help="게시물 관리 진단(미게시 글 감지)")
    pb.add_argument("--dir", default=None)
    pb.add_argument("--board", type=int, default=None, help="리뷰 게시판 번호 (기본: config 또는 4)")
    pb.add_argument("--headed", action="store_true", help="브라우저 보면서")
    pb.add_argument("--url", default=None, help="게시물 관리 URL 직접 지정")

    po = sub.add_parser("open", help="아무 어드민 페이지를 열어 DOM/스크린샷 덤프 (제네릭)")
    po.add_argument("target", help="URL · 경로(/admin/...) · alias(dashboard|boards)")
    po.add_argument("--dir", default=None)
    po.add_argument("--headed", action="store_true", help="브라우저 보면서")
    po.add_argument("--no-referer", action="store_true", help="대시보드 경유 생략")

    pd = sub.add_parser("doctor", help="설정/세션/크로미움 점검")
    pd.add_argument("--dir", default=None)

    sub.add_parser("setup", help="chromium 설치 (최초 1회)")

    pu = sub.add_parser("upgrade", help="cafe24-harness 최신화 (pipx)")
    pu.add_argument("--quiet", action="store_true", help="출력 없이 (훅용)")
    pu.add_argument("--force", action="store_true", help="쿨다운 무시")
    pu.add_argument("--cooldown", type=int, default=0, help="이 초 이내면 스킵 (훅: 21600)")

    ph = sub.add_parser("hook", help="SessionStart 자동 업그레이드 훅 설치/해제")
    ph.add_argument("hook_action", choices=["install", "uninstall"])

    pc = sub.add_parser("claude", help="Claude Code 자산(슬래시 명령어·에이전트)을 ~/.claude 로 설치/갱신")
    pc.add_argument("claude_action", nargs="?", default="install", choices=["install", "refresh"])
    pc.add_argument("--quiet", action="store_true", help="출력 없이 (훅/업그레이드용)")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "init":
        from .commands import init
        return init.run(args)
    if args.cmd == "login":
        from .commands import login
        return login.run(args)
    if args.cmd == "inspect":
        if getattr(args, "target", None) == "board":
            from .commands import inspect_board
            return inspect_board.run(args)
        parser.parse_args(["inspect", "--help"])
        return 1
    if args.cmd == "open":
        from .commands import open as open_cmd
        return open_cmd.run(args)
    if args.cmd == "doctor":
        from .commands import doctor
        return doctor.run(args)
    if args.cmd == "setup":
        return _cmd_setup(args)
    if args.cmd == "upgrade":
        from .commands import upgrade
        return upgrade.run(args)
    if args.cmd == "hook":
        from .commands import hook
        return hook.run(args)
    if args.cmd == "claude":
        from .commands import claude
        return claude.run(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
