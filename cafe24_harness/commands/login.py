"""cf login — headed 브라우저로 사용자가 직접 로그인 → 세션 저장 + 현재 화면 캡쳐."""
from __future__ import annotations

from .. import browser
from ..config import ProjectConfig, resolve_admin_dir


def run(args) -> int:
    cfg = ProjectConfig.load(resolve_admin_dir(args.dir))
    if not cfg.is_configured():
        print("⚠️ config.yaml 의 mall_domain 이 아직 설정 안 됨. `cf init --mall <도메인>` 먼저.")
        return 1
    cfg.ensure_runtime_dirs()
    selectors = cfg.load_selectors()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b, context, page = browser.new_context(p, cfg, headless=False, use_state=True)
        try:
            page.goto(cfg.login_url(), wait_until="domcontentloaded")
        except Exception as e:
            print(f"(이동 중 경고, 무시 가능) {e}")

        print("=" * 64)
        print(" 1) 열린 크롬 창에서 카페24 관리자에 직접 로그인하세요.")
        print(" 2) 진단할 화면(예: 게시판 관리 > 게시물 관리)까지 이동하세요.")
        print(" 3) 그 화면이 보이면 이 터미널로 돌아와 Enter 를 누르세요.")
        print("=" * 64)
        input(">>> 준비됐으면 Enter: ")

        url = page.url
        if "eclogin" in url.lower() or url.rstrip("/").endswith("/admin"):
            print(f"⚠️ 아직 로그인/관리자 홈으로 보임: {url} (세션은 저장합니다)")

        context.storage_state(path=str(cfg.state_file))
        print(f"✅ 세션 저장: {cfg.state_file}")
        print(f"📍 현재 화면 URL: {url}")

        report = browser.dump_page(cfg, page, selectors, "login_capture")
        browser.print_summary(report)
        b.close()
    return 0
