"""cf init — 프로젝트에 페르소나(몰 설정)를 스캐폴드 (멱등).

프로젝트엔 페르소나만 둔다: config.yaml(mall_domain [+ board_no]) + 런타임 디렉토리.
공통 골격(selectors)은 패키지(skeletons/)에 있으므로 프로젝트엔 안 만든다.
SessionStart 자동업그레이드 훅도 (멱등) 등록한다. (--no-hook 으로 생략)
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from ..config import PLACEHOLDER_MALL
from ..urls import SHOP_DEFAULT

GITIGNORE_LINES = [".venv/", "secrets/*.json", "screenshots/", "tmp/", "__pycache__/", "*.pyc"]


def _tmpl(rel: str) -> str:
    return (resources.files("cafe24_harness") / "templates" / rel).read_text(encoding="utf-8")


def _mall_from_url(url: str):
    try:
        return url.split("://", 1)[1].split("/", 1)[0]
    except Exception:
        return None


def _shop_from_url(url: str):
    for marker in ("/disp/admin/", "/php/"):
        if marker in url:
            try:
                return url.split(marker, 1)[1].split("/", 1)[0]
            except Exception:
                pass
    return None


def _derive_from_old_selectors(sel: dict):
    """구버전 selectors(URL 포함)에서 mall/shop/board 추출."""
    mall = shop = None
    board = sel.get("board_no")
    for key in ("admin_login_url", "admin_dashboard_url", "admin_board_list_url"):
        u = sel.get(key)
        if u:
            mall = mall or _mall_from_url(u)
            shop = shop or _shop_from_url(u)
    return mall, shop, (int(board) if board is not None else None)


def run(args) -> int:
    admin_dir = Path(args.dir).resolve()
    cfg_path = admin_dir / "config.yaml"
    results: list[tuple[str, str]] = []

    # 마이그레이션: 구 selectors URL에서 페르소나 추출
    d_mall = d_shop = d_board = None
    if args.migrate:
        sp = admin_dir / "selectors" / "cafe24_board.yaml"
        if sp.exists():
            d_mall, d_shop, d_board = _derive_from_old_selectors(yaml.safe_load(sp.read_text(encoding="utf-8")) or {})

    # 기존 config 값
    e_mall = e_shop = e_board = None
    if cfg_path.exists():
        ec = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        e_mall, e_shop, e_board = ec.get("mall_domain"), ec.get("shop_id"), ec.get("board_no")

    mall = args.mall or d_mall or e_mall or PLACEHOLDER_MALL
    shop = args.shop or d_shop or e_shop or SHOP_DEFAULT
    board = args.board if args.board is not None else (d_board or e_board)  # None 가능

    # 대화형: 몰 도메인만 물어본다 (게시판 번호 등은 안 물어봄 — 그건 작업하며 자동 기록)
    if mall == PLACEHOLDER_MALL and not args.migrate:
        try:
            v = input("카페24 몰 도메인 (예: yourmall.cafe24.com): ").strip()
            if v:
                mall = v
        except EOFError:
            pass

    admin_dir.mkdir(parents=True, exist_ok=True)

    _write_config(cfg_path, mall, shop, board, args.force, results)
    _append_gitignore(admin_dir / ".gitignore", GITIGNORE_LINES, results)
    for sub in ("secrets", "screenshots"):
        d = admin_dir / sub
        d.mkdir(parents=True, exist_ok=True)
        gi = d / ".gitignore"
        if gi.exists():
            results.append((str(gi), "skip(exists)"))
        else:
            gi.write_text("*\n" if sub == "secrets" else "*.png\n*.json\n", encoding="utf-8")
            results.append((str(gi), "created"))

    # 요약
    print(f"\n📂 {admin_dir}")
    for path, status in results:
        icon = "＋" if status in ("created",) else ("·" if status.startswith("skip") else "~")
        rel = str(path).replace(str(admin_dir) + "/", "")
        print(f"  {icon} {rel:<28} {status}")

    # SessionStart 자동업그레이드 훅 (멱등)
    if not getattr(args, "no_hook", False):
        try:
            from . import hook
            print()
            hook.install(args)
        except Exception as e:
            print(f"  (훅 자동등록 스킵: {e} — 수동: cf hook install)")

    print("\n다음 단계:")
    if mall == PLACEHOLDER_MALL:
        print(f"  1. {cfg_path} 의 mall_domain 수정")
    print("  cf login   →   cf open boards (게시판 확인)   →   cf inspect board --board <N>")
    return 0


def _write_config(path: Path, mall, shop, board, force, results):
    """페르소나 기록. 있으면 mall 보충, 없으면 생성. board_no 는 알 때만 적는다."""
    if path.exists() and not force:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cur = data.get("mall_domain")
        if cur in (None, "", PLACEHOLDER_MALL) and mall not in (None, "", PLACEHOLDER_MALL):
            data["mall_domain"] = mall
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            results.append((str(path), "merged(mall 보충)"))
        else:
            results.append((str(path), "skip(exists)"))
        return
    existed = path.exists()
    content = _tmpl("config.yaml.tmpl").replace("{{MALL}}", str(mall))
    extras = []
    if shop and shop != SHOP_DEFAULT:
        extras.append(f'shop_id: "{shop}"')
    if board is not None:
        extras.append(f"board_no: {board}   # 페르소나: 이 몰의 리뷰 게시판 번호")
    if extras:
        content = content.rstrip("\n") + "\n" + "\n".join(extras) + "\n"
    path.write_text(content, encoding="utf-8")
    results.append((str(path), "overwritten(force)" if existed else "created"))


def _append_gitignore(path: Path, lines, results):
    if not path.exists():
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        results.append((str(path), "created"))
        return
    existing = path.read_text(encoding="utf-8").splitlines()
    have = {ln.strip() for ln in existing}
    to_add = [ln for ln in lines if ln.strip() not in have]
    if not to_add:
        results.append((str(path), "skip(all present)"))
        return
    sep = "" if (existing and existing[-1].strip() == "") else "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(sep + "\n".join(to_add) + "\n")
    results.append((str(path), f"appended {len(to_add)} line(s)"))
