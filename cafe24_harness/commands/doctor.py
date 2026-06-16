"""cf doctor — 설정/세션/크로미움 상태 점검 (읽기전용)."""
from __future__ import annotations

import time
from pathlib import Path

from ..config import ProjectConfig, resolve_admin_dir, CONFIG_NAME


def _chromium_ok() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            path = p.chromium.executable_path
            return bool(path) and Path(path).exists()
    except Exception:
        return False


def run(args) -> int:
    admin_dir = resolve_admin_dir(args.dir)
    print(f"📁 프로젝트 admin 디렉토리: {admin_dir}")

    cfg_path = admin_dir / CONFIG_NAME
    if not cfg_path.exists():
        print(f"  ❌ {CONFIG_NAME} 없음 → `cf init --mall <도메인>` 필요")
        return 1
    cfg = ProjectConfig.load(admin_dir)

    ok = True
    # 1. 설정
    if cfg.is_configured():
        print(f"  ✅ mall_domain: {cfg.mall_domain} / shop_id: {cfg.shop_id} / board_no: {cfg.board_no}")
    else:
        print(f"  ❌ mall_domain 미설정(placeholder) → config.yaml 수정 필요")
        ok = False

    # 2. 셀렉터
    sel = cfg.load_selectors()
    print(f"  {'✅' if sel else '⚠️ '} selectors/cafe24_board.yaml: {'로드됨' if sel else '없음/비어있음'}")

    # 3. 세션
    if cfg.has_session():
        age = time.time() - cfg.state_file.stat().st_mtime
        print(f"  ✅ 세션 존재: {cfg.state_file.name} ({int(age // 3600)}시간 전 저장)")
    else:
        print(f"  ❌ 세션 없음 → `cf login` 필요")
        ok = False

    # 4. 크로미움
    if _chromium_ok():
        print("  ✅ chromium 설치됨")
    else:
        print("  ❌ chromium 없음 → `cf setup` 실행")
        ok = False

    print("\n" + ("✅ 정상" if ok else "⚠️ 위 항목 확인 필요"))
    return 0 if ok else 1
