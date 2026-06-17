"""cf init — 프로젝트에 카페24 어드민 설정을 스캐폴드 (멱등).

이미 있는 파일/설정은 절대 중복 생성하지 않는다:
  - config.yaml/selectors/secrets gitignore: 있으면 skip (─-force 만 덮어씀)
  - config.yaml: 있으면 누락 키만 보충(merge), 기존 값 보존
  - .gitignore: append-only (이미 있는 줄은 다시 안 붙임)
  - --migrate: 기존 selectors의 URL에서 mall/board 추출해 config 생성, selectors의 URL 키 제거
"""
from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

from ..config import PLACEHOLDER_MALL
from ..urls import SHOP_DEFAULT

GITIGNORE_LINES = [".venv/", "secrets/*.json", "screenshots/", "tmp/", "__pycache__/", "*.pyc"]
_OLD_URL_KEYS = [
    "admin_login_url", "admin_dashboard_url",
    "admin_board_list_url", "admin_board_setting_url",
    "post_toggle_button",  # 구버전 CSS 셀렉터(현재 id_prefix로 대체)
]


def _tmpl(rel: str) -> str:
    return (resources.files("cafe24_harness") / "templates" / rel).read_text(encoding="utf-8")


def _mall_from_url(url: str) -> str | None:
    # "https://healic.cafe24.com/admin..." -> "healic.cafe24.com"
    try:
        return url.split("://", 1)[1].split("/", 1)[0]
    except Exception:
        return None


def _shop_from_url(url: str) -> str | None:
    # ".../disp/admin/shop1/..." or ".../php/shop1/b/..."
    for marker in ("/disp/admin/", "/php/"):
        if marker in url:
            try:
                return url.split(marker, 1)[1].split("/", 1)[0]
            except Exception:
                pass
    return None


def _derive_from_old_selectors(sel: dict) -> tuple[str | None, str | None, int | None]:
    """구버전 selectors(URL 포함)에서 mall/shop/board 추출."""
    mall = shop = None
    board = sel.get("board_no")
    for key in ("admin_login_url", "admin_dashboard_url", "admin_board_list_url"):
        u = sel.get(key)
        if not u:
            continue
        mall = mall or _mall_from_url(u)
        shop = shop or _shop_from_url(u)
    return mall, shop, (int(board) if board is not None else None)


def run(args) -> int:
    admin_dir = Path(args.dir).resolve()
    sel_path = admin_dir / "selectors" / "cafe24_board.yaml"
    cfg_path = admin_dir / "config.yaml"
    results: list[tuple[str, str]] = []

    # 기존 selectors 로드(있으면)
    old_sel = {}
    if sel_path.exists():
        old_sel = yaml.safe_load(sel_path.read_text(encoding="utf-8")) or {}

    # 마이그레이션: 구 selectors URL에서 추출
    d_mall = d_shop = d_board = None
    if args.migrate:
        d_mall, d_shop, d_board = _derive_from_old_selectors(old_sel)

    # 기존 config 값(있으면)
    e_mall = e_shop = e_board = None
    if cfg_path.exists():
        ec = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        e_mall, e_shop, e_board = ec.get("mall_domain"), ec.get("shop_id"), ec.get("board_no")

    # 우선순위: 인자 > 마이그레이션 추출 > 기존 config > 기본값
    mall = args.mall or d_mall or e_mall or PLACEHOLDER_MALL
    shop = args.shop or d_shop or e_shop or SHOP_DEFAULT
    board = args.board if args.board is not None else (d_board or e_board or 4)

    # 대화형: 몰 도메인이 아직 정해지지 않았고(=플래그·마이그레이션·기존설정 모두 없음)
    # 마이그레이션도 아니면 직접 물어본다. 비대화형(파이프/CI)이면 EOFError → 기본값 유지.
    if mall == PLACEHOLDER_MALL and not args.migrate:
        try:
            print("카페24 몰 정보를 입력하세요 (엔터 = 기본값):")
            v = input("  몰 도메인 (예: yourmall.cafe24.com): ").strip()
            if v:
                mall = v
            v = input(f"  리뷰 게시판 번호 [{board}]: ").strip()
            if v.isdigit():
                board = int(v)
            v = input(f"  shop_id [{shop}]: ").strip()
            if v:
                shop = v
        except EOFError:
            pass  # 비대화형 → 기본/placeholder 유지

    admin_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. config.yaml ---
    _write_config(cfg_path, mall, shop, board, args.force, results)

    # --- 2. selectors/cafe24_board.yaml ---
    _write_selectors(sel_path, old_sel, args.migrate, args.force, results)

    # --- 3. .gitignore (append-only) ---
    _append_gitignore(admin_dir / ".gitignore", GITIGNORE_LINES, results)

    # --- 4. secrets/.gitignore, screenshots/.gitignore + 디렉토리 ---
    for sub in ("secrets", "screenshots"):
        d = admin_dir / sub
        d.mkdir(parents=True, exist_ok=True)
        gi = d / ".gitignore"
        if gi.exists():
            results.append((str(gi), "skip(exists)"))
        else:
            gi.write_text("*\n" if sub == "secrets" else "*.png\n*.json\n", encoding="utf-8")
            results.append((str(gi), "created"))

    # --- 요약 ---
    print(f"\n📂 {admin_dir}")
    for path, status in results:
        icon = {"created": "＋", "skip(exists)": "·", "skip(all present)": "·"}.get(status, "~")
        rel = str(path).replace(str(admin_dir) + "/", "")
        print(f"  {icon} {rel:<32} {status}")

    # --- SessionStart 자동업그레이드 훅 보장 (멱등). --no-hook 으로 생략 ---
    if not getattr(args, "no_hook", False):
        try:
            from . import hook
            print()
            hook.install(args)
        except Exception as e:
            print(f"  (훅 자동등록 스킵: {e} — 수동: cf hook install)")

    print("\n다음 단계:")
    if mall == PLACEHOLDER_MALL:
        print(f"  1. {cfg_path} 의 mall_domain 을 실제 도메인으로 수정")
        print("  2. cf login → cf inspect board")
    else:
        print("  cf login   (headed 로그인)  →  cf inspect board")
    return 0


def _write_config(path: Path, mall, shop, board, force, results):
    if path.exists() and not force:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        changed = False
        for k, v in (("mall_domain", mall), ("shop_id", shop), ("board_no", board)):
            cur = data.get(k)
            missing = (k not in data) or cur in (None, "") or cur == PLACEHOLDER_MALL
            if missing and v not in (None, "") and v != PLACEHOLDER_MALL:
                data[k] = v
                changed = True
        if changed:
            path.write_text(_dump_config(data), encoding="utf-8")
            results.append((str(path), "merged(missing keys)"))
        else:
            results.append((str(path), "skip(exists)"))
        return
    existed = path.exists()
    content = (
        _tmpl("config.yaml.tmpl")
        .replace("{{MALL}}", str(mall))
        .replace("{{SHOP}}", str(shop))
        .replace("{{BOARD}}", str(board))
    )
    path.write_text(content, encoding="utf-8")
    results.append((str(path), "overwritten(force)" if existed else "created"))


def _dump_config(data: dict) -> str:
    # 키 순서 고정 + 주석 없는 단순 덤프(merge 시)
    out = []
    out.append(f'mall_domain: "{data.get("mall_domain", PLACEHOLDER_MALL)}"')
    out.append(f'shop_id: "{data.get("shop_id", SHOP_DEFAULT)}"')
    out.append(f'board_no: {data.get("board_no", 4)}')
    # 그 외 키 보존
    for k, v in data.items():
        if k in ("mall_domain", "shop_id", "board_no"):
            continue
        out.append(yaml.safe_dump({k: v}, allow_unicode=True).strip())
    return "\n".join(out) + "\n"


def _write_selectors(path: Path, old_sel: dict, migrate: bool, force, results):
    if path.exists():
        if migrate and any(k in old_sel for k in _OLD_URL_KEYS):
            cleaned = {k: v for k, v in old_sel.items() if k not in _OLD_URL_KEYS and k != "board_no"}
            path.write_text(yaml.safe_dump(cleaned, allow_unicode=True, sort_keys=False), encoding="utf-8")
            results.append((str(path), "migrated(url 키 제거)"))
        elif force:
            path.write_text(_tmpl("selectors/cafe24_board.yaml.tmpl"), encoding="utf-8")
            results.append((str(path), "overwritten(force)"))
        else:
            results.append((str(path), "skip(exists)"))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_tmpl("selectors/cafe24_board.yaml.tmpl"), encoding="utf-8")
    results.append((str(path), "created"))


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
